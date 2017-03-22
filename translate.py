from textblob.blob import TextBlob
blob = TextBlob('Уровень')
print(str(blob.translate(to='zh-TW')))
