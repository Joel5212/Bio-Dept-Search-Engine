from bs4 import BeautifulSoup
from pymongo import MongoClient
from sklearn.feature_extraction.text import TfidfVectorizer
import nltk
from nltk.stem import WordNetLemmatizer
from nltk import word_tokenize
from bs4 import BeautifulSoup
from pymongo import MongoClient
from sklearn.feature_extraction.text import CountVectorizer
import nltk
nltk.download('omw-1.4')
from nltk.stem import WordNetLemmatizer
from nltk import word_tokenize
nltk.download('punkt')
nltk.download('wordnet')
import pickle

class LemmaTokenizer:
    def __init__(self):
        self.wnl = WordNetLemmatizer()
    def __call__(self, doc):
        # Tokenize the document
        tokens = word_tokenize(doc)
        # Lemmatize and filter out non-alphanumeric tokens
        filtered_tokens = []
        for t in tokens:
            # Include $ symbol and alphanumeric characters
            if t.isalnum() or t == '$':
                filtered_tokens.append(self.wnl.lemmatize(t))
        return filtered_tokens


def connectDataBase():
    # Create a database connection object using pymongo
    DB_NAME = "documents"
    DB_HOST = "localhost"
    DB_PORT = 27017
    try:
        client = MongoClient(host=DB_HOST, port=DB_PORT)
        db = client[DB_NAME]
        return db
    except:
        print("Database not connected successfully...")

def text_transformation():
    # Connect to DB
    db = connectDataBase()
    website_collection = db["websites"]
    inverted_index_collection = db["inverted_index"]
    inverted_index_collection.drop()
    documents_collection = db["documents"]
    documents_collection.drop()

    # Initialize inverted index
    inverted_index = {}

    # Initialize TF-IDF vectorizer
    vectorizer = TfidfVectorizer(ngram_range=(1, 3), tokenizer=LemmaTokenizer(), stop_words='english')

    # Retrieve all faculty member websites
    pages = website_collection.find()
    
    #Relevant text of documents array
    relevant_text_of_documents = []
    
    #All information about the faculty member
    faculty_members_information = []

    # Retrieve relevant/Area of Search text from html
    for page in pages:
        print(page['faculty_member_website_url'])
        bs = BeautifulSoup(page["html"], "html.parser")
        text = bs.find('div', class_='col').get_text(strip = True) + bs.find('div', class_='accolades').get_text(strip = True)
        relevant_text_of_documents.append(text)
        faculty_members_information.append((page['faculty_member_website_url'], page['faculty_member_name'], page['faculty_member_degree_and_focus'], 
                                            page['faculty_member_image_url'], page['faculty_member_phone_number'], page['faculty_member_office_location'], 
                                            page['faculty_member_email_address']))
    
    # learn vocabulary (identifies unique terms) and compute idf values  
    vectorizer.fit(relevant_text_of_documents)

    # Calculate TF-IDF scores
    tfidf_scores_of_documents = vectorizer.transform(relevant_text_of_documents)

    # Get feature names (index terms)
    terms = vectorizer.get_feature_names_out()
    
    for index_of_document, tfidf_scores_of_document in enumerate(tfidf_scores_of_documents.toarray()):
        #Insert the document into the doucment collection (the documents in the collection will be referenced by the terms in the inverted_index)
        new_document_id = documents_collection.insert_one({'faculty_member_website_url': faculty_members_information[index_of_document][0], 
                                                           'faculty_member_name': faculty_members_information[index_of_document][1], 
                                                           'faculty_member_degree_and_focus': faculty_members_information[index_of_document][2],
                                                           'faculty_member_image_url': faculty_members_information[index_of_document][3],
                                                           'faculty_member_phone_number': faculty_members_information[index_of_document][4],
                                                           'faculty_member_office_location': faculty_members_information[index_of_document][5],
                                                           'faculty_member_email_address': faculty_members_information[index_of_document][6],
                                                           'tfidf_scores_of_document': tfidf_scores_of_document.tolist()}).inserted_id
        for index_of_term, tfidf_score_of_document in enumerate(tfidf_scores_of_document):
            if tfidf_score_of_document != 0:
                term = terms[index_of_term]
                #searching for an existing inverted index term 
                inverted_index_id = inverted_index_collection.find_one({"term": term}, {"_id": 1})
                #check if inverted index term already exists
                if inverted_index_id: 
                    inverted_index_collection.update_one({"_id": inverted_index_id['_id']},{"$push":{ "document_ids": new_document_id}})
                else:
                    #Insert each relevant term into the inverted index collection along with the references (ids) to documents
                    inverted_index_collection.insert_one({"term": term, "document_ids": [new_document_id]})  
    
    #storing trained vectorizer model in a pickle file so that it can be used later for information retrieval
    with open('tfidf_vectorizer.pkl', 'wb') as f:
        pickle.dump(vectorizer, f)


    return inverted_index

inverted_index = text_transformation()
    
