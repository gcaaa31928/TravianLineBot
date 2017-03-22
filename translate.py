from textblob.blob import TextBlob
blob = TextBlob('Готово')
print(blob.translate(to='zh-TW'))
