import sys
import pandas
import os

class DropDuplicates:

    def drop_duplicates(self, file_name):
        if os.path.exists(file_name):
            data = pandas.read_csv(file_name, sep=';')
            new_data = data.drop_duplicates(['Unnamed: 0'], keep='last') #pandas names '' as 'Unnamed: 0'
            new_data.rename(columns={'Unnamed: 0': ''}, inplace=True) #rename inplace
            new_data.to_csv(file_name, sep=';', index=False)#export new_data
        else:
            print("Error! " + str(file_name) + " does not exist.")

dropper = DropDuplicates()
dropper.drop_duplicates(sys.argv[1]) #argv[1] --> file_name

#usage: python3 drop_duplicates.py 'filename'