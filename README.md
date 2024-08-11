# astrbot_plugin_english

一个实验性的基于 LLM 和间隔重复记忆算法的英语学习插件。

# 功能

## 单词查询、记录、复习

- 查询单词释义、造句并加入记忆库：`.<word>`，如 `.stunning`
- 复习单词：`..memo`。会根据算法返回 10 个单词。输入 `.<序号> <序号> ...` 可标记遗忘和的单词。如 `.1 2 3`

# 展望

- [ ] 完全实现间隔重复记忆算法
- [ ] 遗忘单词造句、LLM 对话
- [ ] 基于语音的口语对话，语法纠正

# 引用

```bibtex
@inproceedings{10.1145/3534678.3539081,
author = {Ye, Junyao and Su, Jingyong and Cao, Yilong},
title = {A Stochastic Shortest Path Algorithm for Optimizing Spaced Repetition Scheduling},
year = {2022},
isbn = {9781450393850},
publisher = {Association for Computing Machinery},
address = {New York, NY, USA},
url = {https://doi.org/10.1145/3534678.3539081},
doi = {10.1145/3534678.3539081},
abstract = {Spaced repetition is a mnemonic technique where long-term memory can be efficiently formed by following review schedules. For greater memorization efficiency, spaced repetition schedulers need to model students' long-term memory and optimize the review cost. We have collected 220 million students' memory behavior logs with time-series features and built a memory model with Markov property. Based on the model, we design a spaced repetition scheduler guaranteed to minimize the review cost by a stochastic shortest path algorithm. Experimental results have shown a 12.6\% performance improvement over the state-of-the-art methods. The scheduler has been successfully deployed in the online language-learning app MaiMemo to help millions of students.},
booktitle = {Proceedings of the 28th ACM SIGKDD Conference on Knowledge Discovery and Data Mining},
pages = {4381–4390},
numpages = {10},
keywords = {language learning, optimal control, spaced repetition},
location = {Washington DC, USA},
series = {KDD '22}
}
```
