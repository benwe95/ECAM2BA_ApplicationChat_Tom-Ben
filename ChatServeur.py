__author__ = 'Ben&Tom'
import socket
import sys
import struct
import threading
import json
import pickle



SERVERADDRESS=('localhost', 6000)

class Chatserveur():

    def __init__(self):
        self.__s=socket.socket()
        self.__s.bind(SERVERADDRESS)
        #connetedpeople is updated when someone connects or leaves the server
        self.__connectedpeople = set()

    def run(self):
        self.__s.listen()
        while True:
            self.client, self.addr = self.__s.accept()
            try:
                self.handle(self.client)
                self.client.close()
            except:
                print('Error: the server needs to be restarted')

    def handle(self, client):
        try:
            datasize = struct.unpack('I', self.client.recv(4))[0]
            self.data = pickle.loads(self.client.recv(datasize))
            self.selectcommand(self.data)
        except:
            self.datatoclient({'message':''})


    #To launch the right function
    #-pre  parcel is a dictionnary containing the name of the command and sometimes a object with
    #      a piece of data.
    #-post  launches the function
    def selectcommand(self, parcel):
        handlers = {
                    'connectas': self._connectas,
                    'create': self._create,
                    'quit': self._quit,
                    'profil-s': self._profil_s,
                    'profil-e': self._profil_e,
                    'show': self._show,
                    'users': self._users,
                    'contact': self._contact,
                    'showcontacts':self._showcontacts,
                    'quit':self._quit,
                    'private':self._private,
                    'saveconversation':self._saveconversation
                    }
        try:
            handlers[parcel['command']]() if parcel['data'] == None else handlers[parcel['command']](parcel['data'])
        except:
             print("Error: the command couldn't be processed. ")


    #To sends an object to the client
    #-pre  data is a python dictionnary
    #-post  sends the response to the client
    def datatoclient(self, data):
        try:
            dataconverted = pickle.dumps(data)
            self.client.send(struct.pack('I', len(dataconverted)))
            totalsent = 0
            while totalsent < len(dataconverted):
                sent = self.client.send(dataconverted[totalsent:])
                totalsent += sent
        except OSError:
            print("Error: the response couldn't be sent")


    #-pre   data is a 3 elements tuple containing:
    #           - the ID of the client
    #           - his password
    #           - his current address of the client
    #-post  returns a positive answer to the client if the ID exists and matches with the password
    def _connectas(self, data):
        try:
            with open ("usersfile.txt",'r') as usersfile:
                save = json.load(usersfile)
                for user in save:
                    if user==data[0] and save[user]['password']==data[1]:
                        self.__connectedpeople.add(data[0])
                        #Updates the current address of the client
                        save[user]['socket'] = data[2]
                        with open('usersfile.txt','w') as usersoutput:
                            usersoutput.write(json.dumps(save))
                        response = {'message':"You are now connected to the B&T chat\n\n Type '/help' to display the commands.",
                                    'connected':True}
                        return self.datatoclient(response)

                #If the Id couldn't be found in the 'usersfile'
                response = {'message':'Wrong ID or password. Please try again',
                                    'connected':False}
                return self.datatoclient(response)
        except IOError:
            self.datatoclient({'message':'Error server: please try again'})


    #-pre listprofil is a 2 elements list containing:
    #        - the ID of the client
    #        - a dictionnary with his information
    #-post saves the profil in a text file and gives back an answer to the clients
    def _create(self, listprofil):
        try:
            with open ("usersfile.txt",'r') as usersinput:
                save = json.load(usersinput)
                if listprofil[0] not in save:
                    save[listprofil[0]] = listprofil[1]
                else:
                    response = {'message':'ID already used. Please choose another one',
                            'connected':False}
                    self.datatoclient(response)
                    return

            with open ("usersfile.txt",'w') as usersoutput:
                usersoutput.write(json.dumps(save))

            self.__connectedpeople.add(listprofil[0])

            response = {'message':'Your profil has been saved.',
                    'connected':True}
            self.datatoclient(response)
            return

        except:
            self.datatoclient({'message':'Error while creating the profil. Please try again.'})


    #To quit the software
    def _quit(self, ID):
        self.__connectedpeople.remove(ID)
        response = {'message':"""\nYou are now disconnected from the B&T chat.
                    \nSee you soon!""", 'disconnected':True}
        self.datatoclient(response)


    #-pre  ID is the ID of the client
    #-post  returns to the client a dictionnary containing his profil
    def _profil_s(self, ID):
        try:
            with open('usersfile.txt', 'r') as usersinput:
                save = json.load(usersinput)
                for user in save:
                    if user == ID:
                        response = save[user]['profil']

            self.datatoclient(response)
            return

        except:
            self.datatoclient({'message':'Error: please try again.'})


    #-pre  newprofil is a dictionnary containing the new information about the client
    #-post  replaces the old profil by the new one in the 'usersfile'.
    def _profil_e(self, newprofil):
        try:
            with open('usersfile.txt', 'r') as usersinput:
                save = json.load(usersinput)
                for user in save:
                    if user == newprofil[0]:
                        save[user]['profil'] = newprofil[1]
                        response = {'message':'\nYour new profil has been saved'}
                        self.datatoclient(response)

                        with open ("usersfile.txt",'w') as usersoutput:
                            usersoutput.write(json.dumps(save))
                        return
                response = {'message':'\nError: new profil not saved. Please try again'}
        except:
            self.datatoclient({'message':'Error while saving the new profil. Please try again'})


    #-pre  userID is the ID of another user. It must exist
    #-post  sends to the client a dictionnary containing the information about the user
    def _show(self, userID):
        try:
            with open('usersfile.txt', 'r') as usersinput:
                save = json.load(usersinput)
                for user in save:
                    if user == userID:
                        response = save[user]['profil']
                        self.datatoclient(response)
                        return
                response = {'message':"The user couldn't be found. Please verify the ID"}
                self.datatoclient(response)

        except:
            self.datatoclient({'message': 'Error: please try again.'})


    #-pre  /
    #-post  sends to the client the list of the users which are connected
    def _users(self):
        self.datatoclient(self.__connectedpeople)


    #-pre  IDs is a 2 elements list containing:
    #           - the ID of the client
    #           - the ID of the new contact
    #-post  adds the user to the list of contacts
    def _contact(self, IDs):
        try:
            with open('usersfile.txt', 'r') as usersinput:
                save = json.load(usersinput)
                for user in save:
                    if user == IDs[0] and IDs[1] in save:
                        if IDs[1] not in save[user]['contacts']:
                            save[user]['contacts'].append(IDs[1])
                            with open('usersfile.txt','w') as usersoutput:
                                usersoutput.write(json.dumps(save))
                            response = {'message':'\nThe user has been added to your list of contact'}
                            self.datatoclient(response)
                            return
                        else:
                            response = {'message':'\nUser already in your list of contacts.'}
                            self.datatoclient(response)
                response = {'message':"\nError: the user couldn't be found.\nPlease check the ID"}
                self.datatoclient(response)

        except:
            self.datatoclient({'message':'\nError: please try it again.'})


    #-pre ID is the identifiant of the client
    #-post sends to the client his list of contacts sorted by their 'state of connexion' (connected or not)
    def _showcontacts(self, ID):
        connectedcontacts = []
        notconnectedcontacts = []
        try:
            with open('usersfile.txt', 'r') as usersinput:
                save = json.load(usersinput)
                for contact in save[ID]['contacts']:
                    if contact in self.__connectedpeople:
                        connectedcontacts.append(contact)
                    else:
                        notconnectedcontacts.append(contact)
            response = {'connected':connectedcontacts, 'notconnected':notconnectedcontacts}
            self.datatoclient(response)
        except:
            print("error contact-s")


    #-pre  userID is a 2 elements list containing:
    #           - the ID of the client
    #           - the ID of the correspondent
    #-post  sends to the client the 'address' of the correspondent
    def _private(self, userID):
        if userID[1] not in self.__connectedpeople:
            response = {'message':'\nError: the user is not connected.', 'data':(None, None)}
        else:
            with open ('usersfile.txt','r') as usersinput:
                save = json.load(usersinput)
                address = save[userID[1]]['socket']
            with open ('conversations.txt', 'r') as conversationsinput:
                conversationsfile = json.load(conversationsinput)
                for user in conversationsfile:
                    if user == userID[0]:
                        for dest in conversationsfile[user]:
                            #If the client has already chatted with the user
                            if dest == userID[1]:
                                conversation = conversationsfile[user][dest]
                            else:
                                conversation = []

                        response = {'message':'\nEnter your message:\n',
                                    'data':(address, conversation)}
                        self.datatoclient(response)
                        return

                #If the client has never chatted -> creates his save
                conversation = []
                conversationsfile[userID[0]]={}
                conversationsfile[userID[0]][userID[1]] = []
                with open('conversations.txt','w') as conversationsoutput:
                    conversationsoutput.write(json.dumps(conversationsfile))

            response = {'message':'\nEnter your message:\n',
                        'data':(address, conversation)}

        self.datatoclient(response)
        return

    def prepareconversation(self, client, correspondent):
        pass

    #-pre  dataconvers is a 3 elements list containing:
    #           - the ID of the client
    #           - the ID of the correspondent that the client has just chatted with
    #           - the list containing the conversation
    #-post  save the new messages in the 'conversations' file
    def _saveconversation(self, dataconvers):
        with open('conversations.txt','r') as conversationsinput:
            conversationsfile = json.load(conversationsinput)
            listofconversations = conversationsfile[dataconvers[0]][dataconvers[1]]
            #Replaces the old list by the new one
            listofconversations[0:len(listofconversations)+1] = dataconvers[2]
        with open('conversations.txt','w') as conversationsoutput:
            conversationsoutput.write(json.dumps(conversationsfile))

        response = {'message':'Ended conversation'}
        self.datatoclient(response)
        return

if __name__ == '__main__':
    Chatserveur().run()
