__author__ = 'Ben&Tom'
import socket
import sys
import struct
import threading
import json
import pickle
import re
import os
import getpass

SERVERADDRESS=('localhost',6000)

class Chatclient():

    def __init__(self, host='localhost', port=7777):

        self.__address = (socket.gethostbyname(host), port)
        self.__connected = "notconnected"
        self.__ID = None

        cp2p = socket.socket(type=socket.SOCK_DGRAM)
        cp2p.bind(self.__address)
        cp2p.settimeout(0.5)
        self.__cp2p = cp2p


    def run(self):
        print("\nType '/create' to create a new profil or '/connectas <ID>' to connect to your profil.\n")
        self.__running = True
        self.__correspondentaddress = None
        threading.Thread(target=self.receive).start()
        try:
            while self.__running:
                self.line = sys.stdin.readline().rstrip() + ' '
                self.selectcommand(self.line)
            self.__c.close()
        except OSError:
            print("Erreur lors de la connexion avec le serveur")


    def selectcommand(self, line):
        with open('config.json') as file:
            handlers=json.load(file)
        try:
            cmdline = self.analysecommand(line)
            if handlers[cmdline['command']]['status'] == self.__connected:
                try:
                    #Testing if the attribute use is alright
                    testattribut = re.compile(handlers[cmdline['command']]['attribut'])
                    for element in cmdline['attrib']:
                        if testattribut.match(element) == None:
                            raise SyntaxError
                    try:
                        #Testing security of Eval use
                        pattern = r'^[a-z_\.]*$'
                        compilpattern = re.compile(pattern)
                        if compilpattern.match(handlers[cmdline['command']]['command']) == None:
                            raise ValueError
                        if not (type(eval(handlers[cmdline['command']]['command'])) == type(self._help)):
                            raise ValueError
                        try:
                            #Redirection if the command use parameter,attribute or both
                            if (handlers[cmdline['command']]['param']=='yes'):
                                if (handlers[cmdline['command']]['attribut']=="$^"):
                                    eval(handlers[cmdline['command']]['command'])(cmdline['param'])
                                else:
                                    eval(handlers[cmdline['command']]['command'])(cmdline['attrib'],cmdline['param'])
                            else:
                                if (handlers[cmdline['command']]['attribut']=="$^"):
                                    eval(handlers[cmdline['command']]['command'])()
                                else:
                                    eval(handlers[cmdline['command']]['command'])(cmdline['attrib'])
                        except:
                            print("Error: please try again.")
                    except:
                         print("Hacking attempt of the config.json file")
                except:
                    print('Unknown attribut.')
            else:
                print('You must be connected to use the command: ', cmdline['command'])
        except:
            print('Invalid command')


    def analysecommand(self, line):
        line = line.split()
        attribut = []
        param = None
        #Valdiation of the syntax
        if line[0][0] == "/":
            for element in line[1:(len(line)-1)]:
                if not(element[0] == "-"):
                    raise SyntaxError
        else:
            raise SyntaxError

        #Processing of the command line
        for element in line:
            if element[0] == '/':
                command = element
            elif element[0] == '-':
                attribut.append(element)
            else :
                param = element
        #Testing the right use of the command
        with open('config.json') as file:
            config=json.load(file)
        if (config[command]['param']=='yes') and (param==None):
            raise SyntaxError
        if (not attribut) and (not(config[command]['attribut']=="$^")):
            raise SyntaxError
        return {'command' : command,'param' : param, 'attrib' : attribut }


    #-pre  data is a python object
    #-post  Sends the object 'data' to the server and then returns to the user the response from the server
    def datatoserver(self, data):
        try:
            self.__c=socket.socket()
            self.__c.connect(SERVERADDRESS)
            dataconverted = pickle.dumps(data)
            self.__c.send(struct.pack('I', len(dataconverted)))
            totalsent = 0
            while totalsent < len(dataconverted):
                sent = self.__c.send(dataconverted[totalsent:])
                totalsent += sent
            responsesize = struct.unpack('I', self.__c.recv(4))[0]
            response = pickle.loads(self.__c.recv(responsesize))
            self.__c.close()
            return response

        except OSError:
            print("Error: connexion to the server failed")

    #function to test if a string is alpha-numeric
    def alphanumtesting(self,param):
        alphanum = r'^[a-zA-Z0-9]*$'
        alphanumpattern = re.compile(alphanum)
        return alphanumpattern.match(param)

    #Evolution of the input function to a alpha-numeric input function
    #which include a testing and a "re-try" input
    def inputelement(self,string):
        value = input(string)
        while self.alphanumtesting(value) == None :
            print("\n\t-- You must use alpha-numeric character (a-z A-Z 0-9) -- \n" )
            value = input(string)
        return value


    #To connect to the software
    #-pre   the id must exist
    #-post  sends the ID, the password and the current address to the server.
    #       Waits for the response of the server: if it's TRUE (ID has been found and matches
    #        with the password), sets 'self.__connected' to 'connected' else asks the user to retry
    def _connectas(self, ID):
        self.__ID=ID
        password = getpass.getpass("Password: ")
        parcel = {'command':'connectas', 'attrib': [], 'data': (self.__ID, password, self.__address) }
        response = self.datatoserver(parcel)

        os.system('cls' if os.name == 'nt' else 'clear')
        print('\n',response['message'])
        if response['connected']:
            self.__connected = "connected"


    #To create a new profil
    #-pre  /
    #-post  saves the profil and sends it to the server.
    #       The porfil contains the following information:
    #       id, password, socket, contacts, blocked.
    #       The next information can also be completed and will be shown to other users:
    #       firstname, lastname, age, country, profession, hobbies,...
    #       Waits for the response of the server and give back to the user
    def _create(self):
        print("""Create your new profil\n
                (Fields with a '*' must be completed)\n""")
        ID = self.inputelement("\tUsername*: ")
        password = [getpass.getpass("\tPassword*: "), getpass.getpass("\tConfirm password*: ")]
        while not(password[0]==password[1]):
            print("\n\t -- Your confirmation password don't match with the password --\n")
            password = [getpass.getpass("\tPassword*: "), getpass.getpass("\tConfirm password*: ")]
        firstname = self.inputelement("\tFirst Name*: ")
        lastname = self.inputelement("\tLast Name*: ")
        age = self.inputelement("\tAge: ")
        country = self.inputelement("\tCountry: ")
        profession = self.inputelement("\tProfession: ")
        hobbies = self.inputelement("\tHobbies: ")

        importantfields = {'Username':ID,'Password':password[0], 'Confirm password':password[1],
                            'First name': firstname, 'Last name': lastname}
        #verifies if the important fields are completed
        valide = False
        while not valide:
            for element in importantfields:
                if importantfields[element] == '':
                    valide = False
                    importantfields[element] = self.inputelement("\nPlease complete your '{}': ".format(element))
                else:
                    valide = True

        profil = [ID,
                    {
                    'password': password[0],
                    'socket': self.__address,
                    'contacts':[],
                    'blocked':[],
                    'profil':{
                            'First name': firstname,
                            'Last name': lastname,
                            'Age': age,
                            'Country': country,
                            'Profession': profession,
                            'Hobbies': hobbies
                            }
                    }
                  ]

        parcel = {'command': 'create'}

        while self.__connected != 'connected':
            profil[0] = ID
            parcel['data'] = profil
            response = self.datatoserver(parcel)

            #For cleaning the shell window
            os.system('cls' if os.name == 'nt' else 'clear')
            print('\n',response['message'])
            if response['connected']:
                self.__connected = "connected"
            else:
                ID = self.inputelement("\tUsername*: ")

        self.__ID = ID


    #To quit the software
    #-pre  /
    #-post sends a request to te server for lougging out. When it receives a positive answer
    #      quit the application else try again.
    def _quit(self):
        parcel = {'command': 'quit', 'data':self.__ID}
        response = self.datatoserver(parcel)
        os.system('cls' if os.name == 'nt' else 'clear')
        print(response['message'])
        if response['disconnected']:
            self.__connected = 'notconnected'
            self.__running = False
        else:
            print("Please try again.")


    #-pre  attribut must be '-s' or '-e'
    #-post  -shows the user's profil if the attribut is '-s'
    #       -allows the user to edit his profil if attribut is '-e'
    def _profil(self, attribut):
        for element in attribut:
            if element == '-s':
                parcel = {'command':'profil-s', 'data': self.__ID}
                response = self.datatoserver(parcel)
                information = ['First name', 'Last name', 'Age', 'Country', 'Profession', 'Hobbies']
                os.system('cls' if os.name == 'nt' else 'clear')
                for item in information:
                    if response[item] != '':
                        print('\n\t', item, ': ', response[item])

            else:
                os.system('cls' if os.name == 'nt' else 'clear')
                firstname = self.inputelement("\tFirst Name*: ")
                lastname = self.inputelement("\tLast Name*: ")
                age = self.inputelement("\tAge: ")
                country = self.inputelement("\tCountry: ")
                profession = self.inputelement("\tProfession: ")
                hobbies = self.inputelement("\tHobbies: ")
                ask = input("Do you really want to save your new profil? Y/N: ")

                permission = False
                while not permission:
                    if ask == 'Y':
                        permission = True
                        parcel = {'command':'profil-e', 'data':[self.__ID, {'First name': firstname,
                                    'Last name': lastname, 'Age': age,
                                    'Country': country, 'Profession': profession,
                                    'Hobbies': hobbies}]}
                        response = self.datatoserver(parcel)
                        os.system('cls' if os.name == 'nt' else 'clear')
                        print(response['message'])
                    elif ask == 'N':
                        permission = False
                        os.system('cls' if os.name == 'nt' else 'clear')
                        return
                    else:
                        ask = input("""Do you really want to save
                                    your new profil? Y/N: """)


    #To display the profil of another user
    #-pre  id must exist
    #-post  shows the information which are completed
    def _show(self, ID):
        parcel = {'command':'show', 'data':ID}
        response = self.datatoserver(parcel)
        information = ['First name', 'Last name', 'Age', 'Country', 'Profession', 'Hobbies']
        os.system('cls' if os.name == 'nt' else 'clear')
        for item in information:
            if response[item] != '':
                print('\n\t', item, ': ', response[item])


    #-pre  /
    #-post  displays all the users which are connected
    def _users(self):
        parcel = {'command': 'users', 'data':None}
        response = self.datatoserver(parcel)
        sortedusers = []
        for user in response:
            sortedusers.append(user)
        sortedusers.sort()
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\nUser(s) connected:\n")
        for user in sortedusers:
            print('\t', user)


    #-pre   contactID must exist
    #-post  adds the user to the list of contacts if attribut is '-a'
    def _contact(self, contactID):
        parcel = {'command':'contact', 'data':(self.__ID,contactID)}
        response = self.datatoserver(parcel)
        os.system('cls' if os.name == 'nt' else 'clear')
        print(response['message'])


    #shows the list of contacts with their statut of connexion (connected/not connected)
    def _showcontacts(self):
        parcel = {'command': 'showcontacts', 'data': self.__ID}
        response = self.datatoserver(parcel)
        os.system('cls' if os.name == 'nt' else 'clear')

        print("List of contact(s).\n\n\tConnected contact(s):\n")
        if response['connected']!=0:
             for contact in response['connected']:
                print('\t\t', contact)

        print("\n\tNot connected contact(s):\n")
        if response['notconnected']!=0:
            for contact in response['notconnected']:
                print('\t\t', contact)


    #-pre  command must exist
    #-post  displays all the commands.
    def _help(self, command=""):
        os.system('cls' if os.name == 'nt' else 'clear')
        with open("README.md") as file:
            print(file.read())


    ###--------Functions for peer-to-peer chat--------

    #To launch a private conversation with 'anotheruserID'
    #-pre anotheruserID is the Id of the correspondent. It must exist.
    #-post processes the conversation
    def _private(self, anotheruserID):
        self.__destID = anotheruserID
        parcel = {'command':'private', 'data':(self.__ID, anotheruserID)}
        response = self.datatoserver(parcel)
        os.system('cls' if os.name == 'nt' else 'clear')

        if response['data'][0] != None:

            print("Connected to {}. (type '/exit' to end conversation)".format(anotheruserID))
            print(response['message'])
            self.__correspondentaddress = (response['data'][0][0], int (response['data'][0][1]))
            self.__conversation = response['data'][1]
            self.displayconversation()

            active = True
            while active:
                message = sys.stdin.readline().rstrip().split()
                if message[0] == '/exit':
                    active = False
                    self.__correspondentaddress = None
                    newparcel = {'command':'saveconversation', 'data':(self.__ID, anotheruserID, self.__conversation)}
                    exitresponse = self.datatoserver(newparcel)
                else:
                    self.__conversation.append([' '.join(message), self.__ID])
                    #Add the ID of the user at the end of the message for the received process
                    message.append(self.__ID)
                    message = ' '.join(message)
                    self.send(message)

            os.system('cls' if os.name == 'nt' else 'clear')
            print(exitresponse['message'])

        else:
             print(response['message'])


    #-pre  param is the message to send. It's a string
    #-post  sends the message to 'anotheruserID' by using his address (IP, port)
    def send(self, param):
        if self.__correspondentaddress is not None:
            try:
                # self.__conversation.append(param)
                message = param.encode()
                totalsent = 0
                while totalsent < len(message):
                    sent = self.__cp2p.sendto(message[totalsent:], self.__correspondentaddress)
                    totalsent += sent
            except OSError:
                print ("Error: message not sent")


    #To receive messages from anyone.
    #-post  prints the messages if the correspondents are connected together.
    #       saves the messages if they're not.
    def receive(self):
        #The list of message(s) received while the user wasn't connected with the correspondent
        #Each message is stored with the ID of the sender
        self.__newmessages=[]
        #The set of correspondent(s) which tried to reach the user
        self.__newcorresp=set()

        while self.__running:
            try:
                data, address = self.__cp2p.recvfrom(1024)
                data = data.decode().split()
                expID = data[-1]
                del(data[-1])
                data = ' '.join(data)

                #If the users are already connected together print the message received...
                if address == self.__correspondentaddress:
                    print(data.rjust(200))
                #...else warn the user but avoid spamming
                else:
                    self.__newmessages.append([data, expID])
                    if expID not in self.__newcorresp:
                        self.__newcorresp.add(expID)
                        print("\nNew message from: {} \n".format(expID))
            except socket.timeout:
                pass
            except OSError:
                print("Error: exit the conversation and try again.")


    #To display the old conversation
    def displayconversation(self):
        #Makes a copy of the list
        copyconversation = []
        for message in self.__conversation:
            copyconversation.append(message)

        #Prints the messages that were saved on the server. Justifies the text according to the sender
        if len(copyconversation) > 0:
            for message in copyconversation:
                if message[1] == self.__ID:
                    print(message[0])
                elif message[1] == self.__destID:
                    print(message[0].rjust(200))

        #Prints the messages that were sent while the correspondents weren't connected together and
        #saves them in the list of conversations
        if len(self.__newmessages) > 0:
            i = 0
            while i < len(self.__newmessages):
                if self.__newmessages[i][1] == self.__destID:
                    self.__conversation.append(self.__newmessages[i])
                    print((self.__newmessages[i][0]).rjust(200))
                    del(self.__newmessages[i])
                else:
                    i+=1

        if self.__destID in self.__newcorresp:
            self.__newcorresp.remove(self.__destID)



if __name__ == '__main__':
    if len(sys.argv) == 3:
        Chatclient(sys.argv[1], int(sys.argv[2])).run()
    else:
        Chatclient().run()
