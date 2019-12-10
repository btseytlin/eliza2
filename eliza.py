import logging
import random
import re
from config import BotConfig
from collections import namedtuple
from emotion import get_emotion

# Fix Python2/Python3 incompatibility
try: input = raw_input
except NameError: pass
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.DEBUG)
log = logging.getLogger(__name__)


class Key:
    def __init__(self, word, weight, decomps):
        self.word = word
        self.weight = weight
        self.decomps = decomps


class Decomp:
    def __init__(self, parts, save, reasmbs, skip_emotional_reaction, emotions):
        self.parts = parts
        self.save = save
        self.reasmbs = reasmbs
        self.emotions = emotions # A decomp is only applied if the source text had one of the emotions from this list
        self.skip_emotional_reaction = skip_emotional_reaction # If True, will not preppend an acknowledgement of emotions before the response
        self.next_reasmb_index = 0


def strong_emotions_tuples(emotion_dict, threshold=BotConfig.emotion_emotion_threshold):
    emotion_replace = {
        'fear': 'afraid'
    }

    storng_emotions_dict = dict(emotion_dict)
    #e.g. {'Bored': 0.0337543563, 'Sad': 0.0384947692, 'Happy': 0.3989005989, 'Angry': 0.1052993212, 'Excited': 0.276652534, 'Fear': 0.1468984205}
    for key in emotion_dict.keys():
        if emotion_dict[key] < threshold:
            del storng_emotions_dict[key]
    strong_emotions = sorted(list(storng_emotions_dict.items()), key=lambda x: -x[1])
    strong_emotions = [(pair[0].lower().strip(), pair[1]) for pair in strong_emotions]
    strong_emotions = [(emotion_replace.get(pair[0], pair[0]), pair[1]) for pair in strong_emotions]
    return strong_emotions


def sep_punctuation(text):
    text = re.sub(r'\s*\.+\s*', ' . ', text)
    text = re.sub(r'\s*,+\s*', ' , ', text)
    text = re.sub(r'\s*;+\s*', ' ; ', text)
    text = re.sub(r'\s*\?+\s*', ' ? ', text)
    text = re.sub(r'\s*!+\s*', ' ! ', text)
    return text


class Eliza:
    def __init__(self):
        self.initials = []
        self.finals = []
        self.quits = []
        self.pres = {}
        self.posts = {}
        self.synons = {}
        self.keys = {}
        self.memory = []

    def load(self, path):
        key = None
        decomp = None
        with open(path) as file:
            for line in file:
                if not line.strip():
                    continue
                tag, content = [part.strip() for part in line.split(':')]
                content = sep_punctuation(content)
                if tag == 'initial':
                    self.initials.append(content)
                elif tag == 'final':
                    self.finals.append(content)
                elif tag == 'quit':
                    self.quits.append(content)
                elif tag == 'pre':
                    parts = content.split(' ')
                    self.pres[parts[0]] = parts[1:]
                elif tag == 'post':
                    parts = content.split(' ')
                    self.posts[parts[0]] = parts[1:]
                elif tag == 'synon':
                    parts = content.split(' ')
                    self.synons[parts[0]] = parts
                elif tag == 'key':
                    parts = content.split(' ')
                    word = parts[0]
                    weight = int(parts[1]) if len(parts) > 1 else 1
                    key = Key(word, weight, [])
                    self.keys[word] = key
                elif tag == 'decomp':
                    parts = content.split(' ')
                    save = False
                    skip_emotional_reaction = False
                    emotions = []
                    if parts[0] == '$':
                        save = True
                        parts = parts[1:]
                    if parts[0] == '&em_skip':
                        skip_emotional_reaction = True
                        parts = parts[1:]
                    if parts[0] == '&em_only':
                        emotions = parts[1].split('|')
                        parts = parts[2:]
                    decomp = Decomp(parts, save, [], skip_emotional_reaction, emotions)
                    key.decomps.append(decomp)
                elif tag == 'reasmb':
                    parts = content.split(' ')
                    decomp.reasmbs.append(parts)

    def _match_decomp_r(self, parts, words, results):
        if not parts and not words:
            return True
        if not parts or (not words and parts != ['*']):
            return False
        if parts[0] == '*':
            for index in range(len(words), -1, -1):
                results.append(words[:index])
                if self._match_decomp_r(parts[1:], words[index:], results):
                    return True
                results.pop()
            return False
        elif parts[0].startswith('@'):
            root = parts[0][1:]
            if not root in self.synons:
                raise ValueError("Unknown synonym root {}".format(root))
            if not words[0].lower() in self.synons[root]:
                return False
            results.append([words[0]])
            return self._match_decomp_r(parts[1:], words[1:], results)
        elif parts[0].lower() != words[0].lower():
            return False
        else:
            return self._match_decomp_r(parts[1:], words[1:], results)

    def _match_decomp(self, parts, words):
        results = []
        if self._match_decomp_r(parts, words, results):
            return results
        return None

    def _next_reasmb(self, decomp):
        index = decomp.next_reasmb_index
        # result = decomp.reasmbs[index % len(decomp.reasmbs)]
        result = random.choice(decomp.reasmbs)
        # decomp.next_reasmb_index = index + 1
        return result

    def _reassemble(self, reasmb, results, emotion):
        output = []
        for reword in reasmb:
            if not reword:
                continue
            if reword[0] == '(' and reword[-1] == ')':
                index = int(reword[1:-1])
                if index < 1 or index > len(results):
                    raise ValueError("Invalid result index {}".format(index))
                insert = results[index - 1]
                for punct in [',', '.', ';', '?', '!']:
                    if punct in insert:
                        insert = insert[:insert.index(punct)]
                output.extend(insert)
            elif reword == '&em' and emotion:
                output.append(emotion)
            else:
                output.append(reword)
        return output

    def _sub(self, words, sub):
        output = []
        for word in words:
            word_lower = word.lower()
            if word_lower in sub:
                output.extend(sub[word_lower])
            else:
                output.append(word)
        return output

    def _sub_emotion(self, words, emotion):
        output = []
        for word in words:
            word_lower = word.lower()
            if word_lower == '&em':
                output.append(emotion.lower())
            else:
                output.append(word)
        return output

    def _match_key(self, words, key, emotion):
        for decomp in key.decomps:
            if decomp.emotions and emotion not in decomp.emotions:
                log.debug('Input emotion is %s, decomp expected one of %s. Skipped decomp.', emotion, decomp.emotions)
                continue

            results = self._match_decomp(decomp.parts, words)
            if results is None:
                log.debug('Decomp did not match: %s', decomp.parts)
                continue
            log.debug('Decomp matched: %s', decomp.parts)
            log.debug('Decomp results: %s', results)
            results = [self._sub(words, self.posts) for words in results]
            log.debug('Decomp results after posts: %s', results)
            reasmb = self._next_reasmb(decomp)
            log.debug('Using reassembly: %s', reasmb)
            if reasmb[0] == 'goto':
                goto_key = reasmb[1]
                if not goto_key in self.keys:
                    raise ValueError("Invalid goto key {}".format(goto_key))
                log.debug('Goto key: %s', goto_key)
                return self._match_key(words, self.keys[goto_key], emotion)
            output = self._reassemble(reasmb, results, emotion)

            if emotion and not decomp.skip_emotional_reaction:
                reaction_preppend = self._sub_emotion(
                    self._next_reasmb(self.keys['x_sent_reaction'].decomps[0]),
                    emotion)

                output = reaction_preppend + ['\n '] + output
                log.debug('Output with emotion preppend: %s', output)

            if decomp.save:
                self.memory.append(output)
                log.debug('Saved to memory: %s', output)
                continue
            return output
        return None

    def respond(self, text):
        if text.lower() in self.quits:
            return None

        strong_emotions = None
        dominant_emotion = None

        if BotConfig.use_emmotion:
            emotions = get_emotion(text)
            log.debug('Emotions: %s', emotions)
            strong_emotions = strong_emotions_tuples(emotions)
            log.debug('Emotions after filtering: %s', strong_emotions)
            dominant_emotion = strong_emotions[0][0] if strong_emotions else None

        text = sep_punctuation(text)
        log.debug('After punctuation cleanup: %s', text)

        words = [w for w in text.split(' ') if w]
        log.debug('Input: %s', words)

        words = self._sub(words, self.pres)
        log.debug('After pre-substitution: %s', words)

        keys = [self.keys[w.lower()] for w in words if w.lower() in self.keys]
        keys = sorted(keys, key=lambda k: -k.weight)
        log.debug('Sorted keys: %s', [(k.word, k.weight) for k in keys])

        output = None
        for key in keys:
            output = self._match_key(words, key, dominant_emotion)
            if output:
                log.debug('Output from key: %s', output)
                break

        if not output:
            if self.memory:
                index = random.randrange(len(self.memory))
                output = self.memory.pop(index)
                log.debug('Output from memory: %s', output)
            else:
                if strong_emotions:
                    output = self._sub_emotion(self._next_reasmb(self.keys['xnone_sent'].decomps[0]), dominant_emotion)
                    log.debug('Output from xnone with emotion: %s', output)
                else:
                    output = self._next_reasmb(self.keys['xnone'].decomps[0])
                    log.debug('Output from xnone: %s', output)

        out_lines = " ".join(output)
        out_lines = re.sub(r'\s([?.!"](?:\s|$))', r'\1', out_lines) # Remove spaces before punctuation
        return out_lines

    def initial(self):
        return random.choice(self.initials)

    def final(self):
        return random.choice(self.finals)

    def run(self):
        print(self.initial())

        while True:
            sent = input('> ')

            output = self.respond(sent)
            if output is None:
                break

            print(output)

        print(self.final())


def main():
    eliza = Eliza()
    eliza.load('doctor.txt')
    eliza.run()


if __name__ == '__main__':
    logging.basicConfig()
    main()
