data = ["SELL"]
from csv import writer
with open('/home/aryan/acutrade/macd/trades.csv', 'a') as f_object:
     writer_object = writer(f_object)
     writer_object.writerow(data)
     f_object.close()

