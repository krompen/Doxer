from aiogram.dispatcher.filters.state import StatesGroup, State

class ChannelDemolitionStates(StatesGroup):
    channel_link = State()
    option = State()    
    
class RestoreAccountStates(StatesGroup):
    phone = State()
    send_count = State()

class CreateAccountStates(StatesGroup):
    client = State()
    phone = State()
    code = State()
    password = State()

class ReportStates(StatesGroup):
    message_link = State()
    option = State()
    user_id = State()
    message_count = State()
    report_count = State()
    report_reason = State()      
    
class DeleteNonMainSessionStates(StatesGroup):
    SELECT_SESSION = State()
    CONFIRM_DELETE = State()
    
class CheckSessionStates(StatesGroup):
    CHECKING = State()    

class ComplaintStates(StatesGroup):
    subject = State()
    body = State()
    photos = State()
    count = State()
    text_for_site = State()
    count_for_site = State()

class EmailTemplateStates(StatesGroup):
    choose_template = State()
    get_target = State()
    get_violation_url = State()
    get_photo_confirm = State()  
    get_photo = State()         
    get_count = State()

class DeleteSessionStates(StatesGroup):
    SELECT_FOLDER = State()
    SELECT_SESSION = State()
    CONFIRM_DELETE = State()    
            
option_mapping = {
    '1': "1",  
    '2': "2",  
    '3': "3",  
    '4': "4",  
    '5': "5",  
    '6': "6",  
    '7': "7",  
    '8': "8",  
    '9': "9",  
}

reason_mapping = {
    '1': "Spam",
    '2': "Violence",
    '3': "Child Abuse",
    '4': "Pornography",
    '5': "Copyright Infringement",
    '6': "Personal Data Leak",
    '7': "Geo-Irrelevant Content",
    '8': "Fake Information",
    '9': "Illegal Drugs"
}    