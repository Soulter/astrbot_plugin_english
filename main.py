import os, csv, time, json, random, re
import math
from collections import defaultdict
from enum import Enum
from util.plugin_dev.api.v1.bot import Context, AstrMessageEvent, CommandResult
from util.plugin_dev.api.v1.types import *

PLUGIN_PATH = os.path.abspath(__file__)
DATA_PATH = "data/astrbot_plugin_english_data.json"
VOCAB_DIFFICULTY_PATH = os.path.join(os.path.dirname(PLUGIN_PATH), "opensource_dataset_difficulty.tsv")
NAMESPACE = "astrbot_plugin_english"
RETRIEVE_NUM = 20

class MemoryResponse(Enum):
    REMEMBERED = 3
    UNSURE = 2
    FORGOTTEN = 1
    
PROMPT_VOCAB_EXPLAIN = """
ROLE:
你现在是一个专业的英语教师，你需要向学生解释单词的中文释义。

LIMIT:
1. 格式如下：
<word>

n. <释义>
vt. <释义>
adj. <释义>
adv. <释义>

<对该单词的一个造句>

2. 词性释义根据最常见词性按序填写，多个释义用`,`分隔，每个释义为中文且简短。
3. 你的回复只包含以上格式的内容。

EXAMPLE:

abandon

vt. 放弃，抛弃
n. 放纵

He abandoned his wife and children.

TASK:
用户的单词是：{word}
"""

class Main:
    def __init__(self, context: Context) -> None:
        
        self.context = context
        self.context.register_commands(NAMESPACE, r"^\.([a-zA-Z]+)$", "记录英文单词", 1, self.vocab_record, use_regex=True, ignore_prefix=True)
        self.context.register_commands(NAMESPACE, r"\.\.memo", "随机单词", 2, self.memo, use_regex=True, ignore_prefix=True)
        self.context.register_commands(NAMESPACE, r"\.([1-9][0-9]*)(?:\s([1-9][0-9]*))*", "遗忘单词", 1, self.forget, use_regex=True, ignore_prefix=True)

        # load difficulty data
        self.difficulty_data = {}
        with open(VOCAB_DIFFICULTY_PATH, mode='r', encoding='utf-8') as file:
            tsv_reader = csv.DictReader(file, delimiter='\t')
            
            for row in tsv_reader:
                word = row['w']
                difficulty = int(row['d'])
                self.difficulty_data[word] = difficulty

        if not os.path.exists(DATA_PATH):
            with open(DATA_PATH, "w") as f:
                f.write("{}")

        # vocab_data: {<unified_id>: {"<word>": [
        #   [<time>, <response>, <cost>],
        # ]"
        with open(DATA_PATH, "r") as f:
            self.vocab_data = json.load(f)

        self.interactive_cache = {}
            
    async def vocab_record(self, message: AstrMessageEvent, context: Context):
        unified_id = message.unified_msg_origin
        word = message.message_str[1:] # remove the first "."

        if unified_id not in self.vocab_data:
            self.vocab_data[unified_id] = {}
        
        if word not in self.vocab_data[unified_id]:
            self.vocab_data[unified_id][word] = []
        
        self.vocab_data[unified_id][word].append([int(time.time()), MemoryResponse.FORGOTTEN.value, 0])

        with open(DATA_PATH, "w") as f:
            json.dump(self.vocab_data, f)

        llm_instance = None
        for llm in context.llms:
            if llm.llm_name == 'internal_openai':
                llm_instance = llm.llm_instance
                break
        ret = await llm_instance.text_chat(PROMPT_VOCAB_EXPLAIN.format(word=word), session_id=unified_id)

        return CommandResult(
            message_chain=[Plain(ret + "\n" + "已加入记忆库。")],
            use_t2i=False
        )

    async def compute_forget_probability(self, unified_id):
        forget_probabilities = defaultdict(float)
        vocab_data = self.vocab_data[unified_id]
        ts = int(time.time())

        for word, records in vocab_data.items():
            if word not in self.difficulty_data:
                difficulty = 3
            else: difficulty = self.difficulty_data[word]
            difficulty /= 10

            influence_sum = 0
            weighted_sum = 0

            for record in records:
                days_since_review = (ts - record[0]) / 86400
                response_adjustment = 1.0 if record[1] == MemoryResponse.FORGOTTEN.value else 0.5
                influence = math.exp(-0.1 * days_since_review)
                weighted_sum += influence * response_adjustment
                influence_sum += influence            

            if influence_sum > 0:
                P_forget = (weighted_sum / influence_sum) * difficulty
            else:
                P_forget = difficulty

            forget_probabilities[word] = P_forget

        return forget_probabilities

    async def memo(self, message: AstrMessageEvent, context: Context):
        unified_id = message.unified_msg_origin
        if unified_id not in self.vocab_data:
            return CommandResult().message("你还没有记录过任何单词哦")
        
        forget_probabilities = await self.compute_forget_probability(unified_id)
        
        if len(forget_probabilities) == 0:
            return CommandResult().message("你还没有记录过任何单词哦")
        
        # retrieve 10 words randomly based on the forget probabilities using roulette wheel selection
        words = []
        probs = []
        for word, prob in forget_probabilities.items():
            words.append(word)
            probs.append(prob)
        k = min(10, len(words))
        probs = [p / sum(probs) for p in probs]
        selected_words = random.choices(words, weights=probs, k=k)

        ret = "按记忆曲线抽取出单词：\n"
        for idx, word in enumerate(selected_words):
            ret += f"{idx+1}. {word}\n"

        self.interactive_cache[unified_id] = {"selected_words": selected_words, "ts": int(time.time())}

        ret += "`.`开头，遗忘输入单词序号，空格分隔。"

        return CommandResult(
            message_chain=[Plain(ret)],
            use_t2i=False
        )
        
    async def forget(self, message: AstrMessageEvent, context: Context):
        unified_id = message.unified_msg_origin
        if unified_id not in self.interactive_cache:
            return CommandResult().message("请先使用`.memo`命令抽取单词。")

        selected_words = self.interactive_cache[unified_id]["selected_words"]
        forget_words = re.match(r"\.([1-9][0-9]*)(?:\s([1-9][0-9]*))*", message.message_str).groups()
        forget_words = [selected_words[int(idx)-1] for idx in forget_words]

        for word in forget_words:
            if word in self.vocab_data[unified_id]:
                interval = int(time.time()) - self.interactive_cache[unified_id]["ts"]
                self.vocab_data[unified_id][word].append([int(time.time()), MemoryResponse.FORGOTTEN.value, interval])

        with open(DATA_PATH, "w") as f:
            json.dump(self.vocab_data, f)

        return CommandResult().message("已更新遗忘记录。")
        