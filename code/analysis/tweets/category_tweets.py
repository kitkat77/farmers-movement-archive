import pandas as pd
import math
import matplotlib.pyplot as plt
import numpy as np
import datetime
from tweet_cleaning import clean_tweet

class Category():
	def __init__(self, name):
		print("!!!!! initializing category : ", name)
		self.name = name
		self.usernames = []
		self.n_tweets = 0
		self.n_usernames = 0
		self.tweets = pd.DataFrame(columns = ['username', 'tweet'])

	def retrieve_count(self, categories_df, counts_df):						# get n_tweets, n_usernames and usernames
		df = categories_df.loc[categories_df['category'] == self.name]
		for index, row in df.iterrows():									# for every row with this category
			username = row['username']

			self.usernames.append(username)									# update usernames array
			self.n_usernames += 1											# update n_usernames array
			
			temp_df = counts_df.loc[counts_df['username'] == username]		# get corresponding count from counts_df 
			for i,r in temp_df.iterrows():
				self.n_tweets += r['count']									# add to n_tweets variable in category
				break
		print("* username count as calculated : ", self.n_usernames)
		print("* tweet count as calculated : ", self.n_tweets)

	def get_date_tweets(self, dir_path, date):								# get df of a day's tweets
		date_string = date.strftime("%Y-%m-%d")
		month_string = date.strftime("%Y-%m")
		filepath = dir_path + '/' + month_string + '/' + date_string + '/combined.csv'
		df = pd.read_csv(filepath, lineterminator='\n')
		return df

	def update_tweets(self, date_df):										# add tweets of category to self.tweets df
		date_df = date_df[['username', 'tweet']]
		df = date_df[date_df['username'].isin(self.usernames)]
		self.tweets = pd.concat([self.tweets, df])
		return

	def retrieve_tweets(self):												# retrieve all tweets and add ones of category to self.tweets
		start_string = '01-09-2020'
		end_string = '28-02-2022'
		dir_path = '../../../corpus/verified_tweets'
		
		start_date = datetime.datetime.strptime(start_string, "%d-%m-%Y")
		end_date = datetime.datetime.strptime(end_string, "%d-%m-%Y")
		date = start_date
		while date <= end_date:
			cur_df = self.get_date_tweets(dir_path, date)
			self.update_tweets(cur_df)
			date += datetime.timedelta(days=1)

		print("* tweets collected for category : ", len(self.tweets))

	def get_word_counts(self):												# get word frequencies
		print("* intitiating retrieval of word counts for category : ", self.name)
		word_counts = {}
		for index, row in self.tweets.iterrows():
			tweet = row['tweet']
			words = clean_tweet(tweet)
			for word in words:
				if word not in word_counts.keys():
					word_counts[word] = 0
				word_counts[word] += 1
		print("* finished retrieving word counts for category : ", self.name)
		return word_counts

	def print_word_counts(self, filepath):									# print word frequencies
		word_counts = self.get_word_counts()
		word_counts = dict(sorted(word_counts.items(), key=lambda item: item[1], reverse=True))
		file = open(filepath, 'w')
		for word in word_counts.keys():
			to_write = '|'.join([word, str(word_counts[word])]) + '\n'
			file.write(to_write)
		file.close()
		print("* finished printing word counts for category : ", self.name)


def print_line():
	print("-"*20)

def get_categories():
	counts_df = pd.read_csv('results/counts.txt', lineterminator='\n', sep='\|')

	categories_df = pd.read_csv('categories.csv', lineterminator='\n')
	categories_df.dropna(subset=['category'])
	categories_df.drop(categories_df.columns.difference(['username','category']), 1, inplace=True)
	categories_df.drop(categories_df.index[categories_df['category'] == '\r'], inplace=True)
	categories_df = categories_df[categories_df['category'].notna()]
	categories_df['category'] = categories_df['category'].apply(lambda x: x.strip())
	# print(categories_df)

	category_names = list(categories_df['category'].unique())
	# print(category_names)
	categories = []
	for name in category_names:
		category = Category(name)
		category.retrieve_count(categories_df, counts_df)
		category.retrieve_tweets()
		categories.append(category)
		print_line()

	return categories

def print_all_word_counts(categories):
	for category in categories:
		name = category.name
		if '/' in name:
			name = name.replace('/', '-')
		filepath = 'results/words/' + name
		category.print_word_counts(filepath)

categories = get_categories()
print_all_word_counts(categories)