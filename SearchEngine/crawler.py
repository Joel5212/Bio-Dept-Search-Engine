from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.error import URLError
from bs4 import BeautifulSoup
import re
from pymongo import MongoClient


def crawler_thread (frontier):
    
    visited_urls = set()
    
    while frontier:
        try:
            url = frontier.pop(0)
            
            #since there are urls with only the directory of the webpage we need to append the schema and domain so we can open the full url
            
            if 'https://' not in url and 'http://' not in url:
                
                # print("APPENDING URL")
                
                #checking if the urls with only the directory starts with "/"
                if url[0] != "/":
                    url = 'https://www.cpp.edu/' + url  
                else:
                    url = 'https://www.cpp.edu' + url  
                    
            if ('https://www.cpp.edu' in url or 'http://www.cpp.edu' in url) and url not in visited_urls:
                
                #making sure we don't visit already visited urls
                visited_urls.add(url)  
            
                #save html document in the html variable             
                html = urlopen(url)
            
                bs = BeautifulSoup(html.read(), 'html.parser')
            
                #if the Biological Science Department Faculty Page is found discard the current frontier, implemented this so we don't go through a lot of unncessary urls
                if bs.find(re.compile('h[1-6]'), string=re.compile('Biological Sciences Tenure-Track Faculty')):
                    frontier.clear()
                    
                    for div in bs.findAll('div', class_ = 'card h-100'):
                        
                        #extract faculty member's phone number
                        faculty_member_details = div.findAll('li')
                        
                        faculty_member_website_anchor_tag = faculty_member_details[len(faculty_member_details) - 1].find(string=re.compile('Website'))
                        
                        #check to see if there is a website link otherwise just skip
                        if faculty_member_website_anchor_tag == None:
                            continue
                        else:
                            faculty_member_website_url = faculty_member_website_anchor_tag.parent.get('href')
      
                        #since there are urls with only the directory of the webpage we need to append the schema and domain so we can open the full url
                        if 'https://' not in  faculty_member_website_url and 'http://' not in  faculty_member_website_url:
                            
                            print("APPENDING URL")
                
                            #checking if the urls with only the directory starts with "/"
                            if  faculty_member_website_url[0] != "/":
                                faculty_member_website_url = 'https://www.cpp.edu/' + faculty_member_website_url  
                            else:
                                faculty_member_website_url = 'https://www.cpp.edu' + faculty_member_website_url  

                        try:
                            #check to see if the faculty member website link is directed to the target otherwise skip
                            html = urlopen(faculty_member_website_url)
                            bs = BeautifulSoup(html.read(), 'html.parser')
                            html_string = str(bs)
                            
                            fac_info = bs.find('div', class_ = 'fac-info')
                            
                            # if not fac_info or not all(fac_info.find('p', class_ = cls) for cls in ['emailicon', 'phoneicon', 'locationicon', 'hoursicon']):
                            if not fac_info or not all(fac_info.find('p', class_=cls) for cls in ['emailicon', 'phoneicon', 'locationicon', 'hoursicon']):
                                continue
                        except Exception as e:
                            print(str(e) + " - " + faculty_member_website_url)
                            continue
                        
                        #extract faculty member's name
                        faculty_member_name = div.find('h3').get_text(strip = True)
                        
                        #extract faculty member's degree and focus
                        faculty_member_degrees_and_focuses = div.findAll('div', class_ = 'mb-1 text-muted')
                        
                        combined_faculty_member_degrees_and_focuses = ""
                    
                        for index, faculty_member_detail in enumerate(faculty_member_degrees_and_focuses):
                            
                            faculty_member_degrees_and_focus_string = faculty_member_detail.get_text(strip = True)
                            
                            #do not add the " | " unless if there are more than 1 degrees_and_focus and if its not the last one
                            if len(faculty_member_degrees_and_focuses) != 1 and index != len(faculty_member_degrees_and_focuses) - 1:
                                combined_faculty_member_degrees_and_focuses += faculty_member_degrees_and_focus_string + " | "
                            else: 
                                combined_faculty_member_degrees_and_focuses += faculty_member_degrees_and_focus_string
                        
                        #extract image url
                        image_url = div.find('img').get('src')
                        full_image_url = image_url.replace("../", "	https://www.cpp.edu/sci/biological-sciences/").strip()

                        #extract phone number, office location, and email address (some info might not be included)
                        faculty_member_phone_number = None
                        
                        faculty_member_office_location = None
                        
                        faculty_member_email_address = None
                        
                        for faculty_member_detail in faculty_member_details:
                            
                            detail_type = faculty_member_detail.find('span', class_ = "sr-only").get_text(strip = True)
                            
                            text = faculty_member_detail.get_text(strip = True)
                            
                            if detail_type == "phone number or extension":
                                faculty_member_phone_number = text.replace("phone number or extension", " ").strip()
                            elif detail_type == "office location":
                                faculty_member_office_location = text.replace("office location", " ").strip()
                            elif detail_type == "email address":
                                faculty_member_email_address = text.replace("email address", " ").strip()
                        
                        #store each faculty member target webpage into mongodb
                        db.websites.insert_one({'html':html_string, 'faculty_member_website_url': faculty_member_website_url,
                                                'faculty_member_name': faculty_member_name, 'faculty_member_degree_and_focus': combined_faculty_member_degrees_and_focuses, 'faculty_member_image_url': full_image_url, 
                                                'faculty_member_phone_number': faculty_member_phone_number, 'faculty_member_office_location': faculty_member_office_location,
                                                'faculty_member_email_address': faculty_member_email_address})
                else:
                    for a in bs.findAll('a', href = re.compile('.html')):
                        frontier.append(a['href'])
        except Exception as e:
            print(str(e) + " - " + url)
            continue
            
            
db = MongoClient(host = "localhost", port = 27017).documents

#Dropping the websites collection everytime we run the crawler process
db.websites.drop()

#open the webpage of the seed url
html = urlopen('https://www.cpp.edu/sci/')
bs = BeautifulSoup(html.read(), 'html.parser')

frontier = [a['href'] for a in bs.findAll('a', href = re.compile('.html'))]

#running the crawler process
crawler_thread(frontier)
