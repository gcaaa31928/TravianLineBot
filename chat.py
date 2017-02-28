from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer

chatbot = ChatBot("myBot")
chatbot.set_trainer(ChatterBotCorpusTrainer)

chatbot.train("chatterbot.corpus.chinese")

