from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer

chatbot = ChatBot("myBot")
chatbot.set_trainer(ChatterBotCorpusTrainer)

# 使用英文语料库训练它
chatbot.train("chatterbot.corpus.chinese")

# 开始对话
print(chatbot.get_response("你住哪裡"))
