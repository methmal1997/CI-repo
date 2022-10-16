import PyPDF2
import nltk
import re
import string
import pandas as pd
import csv
import os
from nltk import word_tokenize
from PyPDF2 import PdfFileReader
import boto3
from io import BytesIO
from io import StringIO 
import string


import nltk
nltk.download('punkt')



s3 = boto3.resource(
    service_name='s3',
    region_name='us-east-2',
    aws_access_key_id='AKIAWGMDI5C4RJTLTYTN',
    aws_secret_access_key='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'
)


class Extracting:
    
    '''    In this class pdf and text files letter extracted and save into csv file according to parent file Name,
        If there is already build csv then new data should append to exiting one. If not created new one CSV file 
        and save into to that'''
   
    def __init__(self,job_category):
        self.job_category = job_category
        self.sentances = pd.DataFrame()

        
        
    def read(self,obj2):
        # for obj in s3.Bucket('resumedatadatadisca').objects.filter(Prefix='profession/'+self.job_category+'/'):
        fs = obj2.get()['Body'].read()
        try:
            pdfFile = PdfFileReader(BytesIO(fs))
            pageObj = pdfFile.getPage(0)
            keys=pageObj.extractText()
            data = re.sub('\[.*?\]','',keys)
            data = data.translate(str.maketrans('', '', string.punctuation))
            #remove punctuation marks
            data = re.sub('\w*\d\w*','',data)
            #remove numbers
            data = re.sub('[^a-zA-Z\d\s.]','',data).lower()
            return data
        except Exception:
            print("failed")
            pass
        
        

    def write_csv(self):
        
        filename ='dataset.csv'
        for obj in s3.Bucket('resumedatadatadisca').objects.filter(Prefix='profession/'+self.job_category+'/'):
            data=Extracting.read(self,obj)


            try:
        
                obj = s3.Bucket('resumedatadatadisca').Object(filename).get()
                old_df = pd.read_csv(obj['Body'], index_col=0)
                new_row = {'profession':self.job_category, 'data':data}
                #append row to the dataframe
                old_df = old_df.append(new_row, ignore_index=True)
                csv_buffer = StringIO()
                old_df.to_csv(csv_buffer)
                s3.Object("resumedatadatadisca", 'dataset.csv').put(Body=csv_buffer.getvalue())

                print("Updated dataframe is saved as CSV in S3 bucket.")

                
            except:
                
                column = ['index','profession','data']
                row=["1",self.job_category,data]
                with open(filename, 'w') as file:
                    # 2. Create a CSV writer
                    writer = csv.writer(file)
                    # 3. Write data to the file
                    writer.writerow(column) # make a new file if not
                    writer.writerow(row)
                s3.Bucket('resumedatadatadisca').upload_file(Filename = filename,Key = filename)
                print('New dataFrame Created and saved as CSV')
                
class Importing_csv:
    
    '''
    Here importing CSV file and tokeniz it. After that it gone with preprosses stage
    '''
    
    def __init__(self,dataset_name):
        obj = s3.Bucket('resumedatadatadisca').Object(dataset_name).get()
        self.df = pd.read_csv(obj['Body'], index_col=0)
    
    def tokniz(self):
        self.df['tokenized_data'] = self.df.apply(lambda row: word_tokenize(row['data']), axis=1)
        #tokniz data column and create new column for that tokniz_data
        return self.df
    
    def preprocess(self):
        # df = Importing_csv.tokniz(self)
        df=self.df
        df=df.dropna().reset_index()
        del df['index']
        df.drop_duplicates()
        #remove null and duplicate values

        # drop data column which hasn't tokniz and return result DF
        return df
        