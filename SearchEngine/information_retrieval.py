from sklearn.metrics.pairwise import cosine_similarity
from flask import Flask, request, jsonify
import json 
from nltk.stem import WordNetLemmatizer
from nltk import word_tokenize
from pymongo import MongoClient
import re;
from bson import ObjectId
from flask import Flask, jsonify
from flask_cors import CORS
import pickle


app = Flask(__name__)
cors = CORS(app)

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


with open('tfidf_vectorizer.pkl', 'rb') as f:
    tfidf_vectorizer = pickle.load(f)
    
def connect_database():
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

def compare_query_and_relevant_documents(query):
    db = connect_database()
    inverted_index_collection = db["inverted_index"]
    documents_collection = db["documents"]
    
    #storing relevant documents ids
    relevant_document_ids = set()
    
    #storing relevant document vectors from documents collection
    relevant_document_vectors = []
    
    #storing the relevant faculty members' details
    faculty_member_details = []
    
    query_list = [query]

    #Transform query into its tf-idf vector using the tfidf vectorizer model
    tfidf_scores_of_query = tfidf_vectorizer.transform(query_list).toarray()[0]
    
    #Get the terms
    terms = tfidf_vectorizer.get_feature_names_out()

    #Fetch all inverted index documents based on query and extract all the document ids of the relevant terms in the inverted index
    for i, tfidf_score_of_query in enumerate(tfidf_scores_of_query):
        if tfidf_score_of_query != 0:
            term = terms[i]
            inverted_index_document = inverted_index_collection.find_one({"term": term})
            for document_id in inverted_index_document.get("document_ids"):
                if document_id not in relevant_document_ids:
                    relevant_document = documents_collection.find_one({"_id": document_id})
                    faculty_member_details.append((relevant_document.get('faculty_member_website_url'),
                                                   relevant_document.get('faculty_member_name'),
                                                   relevant_document.get('faculty_member_degree_and_focus'), 
                                                    relevant_document.get('faculty_member_image_url'),
                                                    relevant_document.get('faculty_member_phone_number'),
                                                    relevant_document.get('faculty_member_office_location'),
                                                    relevant_document.get('faculty_member_email_address')))
                    
                    relevant_document_vector = relevant_document.get('tfidf_scores_of_document')
                    relevant_document_vectors.append(relevant_document_vector)
                    relevant_document_ids.add(document_id)

    relevant_document_vectors.append(tfidf_scores_of_query.tolist())
    
    cos_sim = cosine_similarity(relevant_document_vectors)
    
    len_of_cos_sim = len(cos_sim)-1
    
    unsorted_results = {}
    
    sorted_results = []
    
    for i, sim_score in enumerate(cos_sim[len_of_cos_sim]):
        if i != len_of_cos_sim:
           unsorted_results[faculty_member_details[i][0]] = (faculty_member_details[i][1], faculty_member_details[i][2], faculty_member_details[i][3], 
                                                             faculty_member_details[i][4], faculty_member_details[i][5], faculty_member_details[i][6], sim_score)
               
    sorted_results = sorted(unsorted_results.items(), key=lambda x: x[1][6], reverse=True)
    
    return sorted_results
        
@app.route('/retrieve-relevant-documents', methods = ['POST'])
def retrieve_relevant_documents():
    data = request.json
    relevant_documents = compare_query_and_relevant_documents(data)
    
    print("RESULTS: ", relevant_documents)
    
    return jsonify({
        'relevant_documents': relevant_documents
    })

if __name__ == '__main__':
    app.run(port=2000)     
        
        
        
        
        
    
    