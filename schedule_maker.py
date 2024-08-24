from PIL import Image, ImageDraw, ImageFont
import json 
import os
from CrudWrapper import parse_timestamp, CrudWrapper
import random
import pytz
import datetime


crudService = CrudWrapper("DEV_REMOTE","","")


class Rectangle:
    def __init__(self) -> None:
        self.top_left = (0,0)
        self.width = 0
        self.height = 0

        self.top = None
        self.left = None
        self.right = None
        self.bottom = None

    def __str__(self):
        print(self.top_left, self.width, self.height)

        return ""

    def get_json(self):
        return {"top_left":[self.top_left[0],self.top_left[1]],"width":self.width,"height":self.height,
                     "top":self.top,"left":self.left,"right":self.right,"bottom":self.bottom}
    
    
    def load_from_json(self,json_obj):
        self.top_left = (json_obj["top_left"][0],json_obj["top_left"][1])

        self.width = json_obj["width"]
        self.height = json_obj["height"]

        self.top = json_obj["top"]
        self.left = json_obj["left"]
        self.right = json_obj["right"]
        self.bottom = json_obj["bottom"]

class Layout:
    def __init__(self,logo_rect=None,art_rect=None,schedule_rect=None,date_rect=None,name_rect=None,time_rect=None) -> None:
        self.logo_rect = logo_rect
        self.art_rect = art_rect
        self.schedule_rect = schedule_rect
        self.date_rect = date_rect
        self.name_rect = name_rect
        self.time_rect = time_rect
        self.font_color = None 
        self.image_size = None
        
    def get_json(self):
        return {"logo":self.logo_rect.get_json(),"art":self.art_rect.get_json(),"schedule":self.schedule_rect.get_json(),
                "date":self.date_rect.get_json(),"name":self.name_rect.get_json(),"time":self.time_rect.get_json(),
                "font_color":self.font_color,"size":self.image_size}
    
    def load_from_json(self,json_obj):
        self.logo_rect = Rectangle()
        self.logo_rect.load_from_json(json_obj["logo"])

        self.art_rect = Rectangle()
        self.art_rect.load_from_json(json_obj["art"])

        self.schedule_rect = Rectangle()
        self.schedule_rect.load_from_json(json_obj["schedule"])

        self.date_rect = Rectangle()
        self.date_rect.load_from_json(json_obj["date"])

        self.name_rect = Rectangle()
        self.name_rect.load_from_json(json_obj["name"])

        self.time_rect = Rectangle()
        self.time_rect.load_from_json(json_obj["time"])

        self.font_color=json_obj["font_color"]
        self.image_size=json_obj["size"]

def text_size_bigger(streamer_path,words,max_width,max_height,size):
    while True:
        nameFont = ImageFont.truetype(streamer_path+'font.ttf', size)
        bbox = nameFont.getbbox(words)

        curr_height = bbox[3] - bbox[1]
        curr_width = bbox[2] - bbox[0]

        if curr_height > max_height or curr_width > max_width:
            return ImageFont.truetype(streamer_path+'font.ttf', size-1)

        size +=1

def text_size_smaller(streamer_path,words,max_width,max_height,size):
    while True:
        nameFont = ImageFont.truetype(streamer_path+'font.ttf', size)
        bbox = nameFont.getbbox(words)

        curr_height = bbox[3] - bbox[1]
        curr_width = bbox[2] - bbox[0]

        if curr_height <= max_height and curr_width <= max_width:
            return ImageFont.truetype(streamer_path+'font.ttf', size)

        size -=1

def get_correct_size(streamer_path,words,max_width,max_height):
    size = 40
    nameFont = ImageFont.truetype(streamer_path+'font.ttf', size)
    bbox = nameFont.getbbox(words)

    curr_height = bbox[3] - bbox[1]
    curr_width = bbox[2] - bbox[0]

    if curr_height <= max_height and curr_width <= max_width:
        return text_size_bigger(streamer_path,words,max_width,max_height,size)
    else:
        return text_size_smaller(streamer_path,words,max_width,max_height,size)
        
def create_layout_json(streamer_base_path):

        
    def populate_Rectangle(rectangle):
            if(rectangle.top == None or rectangle.top > y):
                rectangle.top = y
            if(rectangle.bottom == None or rectangle.bottom < y):
                rectangle.bottom = y

            if(rectangle.left == None or rectangle.left > x):
                rectangle.left = x
            if(rectangle.right == None or rectangle.right < x):
                rectangle.right = x

    # get width, height, and top left
    def rectangle_postProcess(rectangle):
        rectangle.width = rectangle.right-rectangle.left 
        rectangle.height = rectangle.bottom-rectangle.top 
        rectangle.top_left = (rectangle.left,rectangle.top)    

    
    # Open image and get details
    layout_image = Image.open(streamer_base_path+"layout.png")   
    width, height = layout_image.size

    # figure out if we found a new maximum/minimum
   

    # define the areas
    logo_rect = Rectangle()
    art_rect = Rectangle()
    schedule_rect = Rectangle()

    #iterate through image, saving layour information
    for x in range(width):
        for y in range(height):
            r,g,b,a = layout_image.getpixel((x,y))

            # Logo
            if r == 255 and b == 0 and g == 0:
                populate_Rectangle(logo_rect)

            # art
            if r == 0 and b == 255 and g == 255:
                populate_Rectangle(art_rect)

            # shceduled 
            if r == 255 and b == 0 and g == 255:
                populate_Rectangle(schedule_rect)

    rectangle_postProcess(logo_rect)
    rectangle_postProcess(art_rect)
    rectangle_postProcess(schedule_rect)


    # open box image
    box_image = Image.open(streamer_base_path+"box.png")   


    # see how tall each box can be
    max_indiv_height = schedule_rect.height / 7

    # determine best scale factor
    scaling_factor_x = box_image.width / schedule_rect.width
    scaling_factor_y = box_image.height / max_indiv_height

    scale_factor = max(scaling_factor_x,scaling_factor_y)

    # determine box new image size
    new_x = box_image.width * (1/scale_factor)
    new_y = box_image.height * (1/scale_factor)

    box_scaled = box_image.resize((int(new_x),int(new_y)))
    box_scaled.save(streamer_base_path+"box_scaled.png")

    box_layout_image = Image.open(streamer_base_path+"box_layout.png")   
    box__layout_scaled = box_layout_image.resize((int(new_x),int(new_y)))
    box__layout_scaled.save(streamer_base_path+"box_layout_scaled.png")


    box_width, box_height = box__layout_scaled.size

    date_rect = Rectangle()
    name_rect = Rectangle()
    time_rect = Rectangle()
    # get layout data from new box asset
    for x in range(box_width):
        for y in range(box_height):
            r,g,b,a = box__layout_scaled.getpixel((x,y))

            # date
            if r == 0 and b == 0 and g == 255:
                populate_Rectangle(date_rect)

            # name
            if r == 0 and b == 255 and g == 0:
                populate_Rectangle(name_rect)

            # time 
            if r == 255 and b == 255 and g == 0:
                populate_Rectangle(time_rect)


    rectangle_postProcess(date_rect)
    rectangle_postProcess(name_rect)
    rectangle_postProcess(time_rect)


    # add stuff to layout class
    layout = Layout(logo_rect,art_rect,schedule_rect,date_rect,name_rect,time_rect)

    font_color = layout_image.getpixel((0,0))
    layout.font_color = font_color

    final_size = layout_image.size
    layout.image_size = final_size


    json_obj = layout.get_json()
    json_file = open(streamer_base_path+"layout.json","w")
    json.dump(json_obj,json_file)
    json_file.close()

    
    return layout


def resize_to_fit(image, max_width,max_height,min_flag):
    # determine best scale factor
    scaling_factor_x = image.width / max_width
    scaling_factor_y = image.height / max_height

    if(min_flag):
        scale_factor = min(scaling_factor_x,scaling_factor_y)
    else:
        scale_factor = max(scaling_factor_x,scaling_factor_y)

    # determine box new image size
    new_x = image.width * (1/scale_factor)
    new_y = image.height * (1/scale_factor)

    image_scaled = image.resize((int(new_x),int(new_y)))

    return image_scaled

def make_schedule(streamer,streams):
    # Get streamer's base path
    base_path = "assets/"

    if(os.path.exists("assets/"+streamer.guild+"/")):
        streamer_guild = streamer.guild+"/"

        streamer_base_path = base_path + streamer_guild
    else:
        streamer_base_path = base_path + "default/"

    layout_json_exists = os.path.exists(streamer_base_path+"layout.json")



    if not layout_json_exists:
        layout = create_layout_json(streamer_base_path)
    else:
        layout = Layout()

        json_file = open(streamer_base_path+"layout.json")
        json_data = json.load(json_file)
        json_file.close()

        layout.load_from_json(json_data)


    # start compositing

    schedule_image = Image.new("RGBA",layout.image_size)

    ########################################### PLACE BG  ###########################################################

    all_bgs = os.listdir(streamer_base_path+"bg/")
    bg_choice = random.choice(all_bgs)

    bg_image = Image.open(streamer_base_path+"bg/"+bg_choice)

    bg_image_scaled = resize_to_fit(bg_image,layout.image_size[0],layout.image_size[1],True)
    schedule_image.alpha_composite(bg_image_scaled)

    ########################################### PLACE ART ###########################################################

    all_arts = os.listdir(streamer_base_path+"art/")
    art_choice = random.choice(all_arts)

    art_image = Image.open(streamer_base_path+"art/"+art_choice)

    art_image_scaled = resize_to_fit(art_image,layout.art_rect.width,layout.art_rect.height,False)
    schedule_image.alpha_composite(art_image_scaled,(layout.art_rect.top_left[0],layout.art_rect.top_left[1]+(layout.art_rect.height-art_image_scaled.height)))

    ########################################### PLACE LOGO ###########################################################

    logo_image = Image.open(streamer_base_path+"logo.png")
    logo_image_scaled = resize_to_fit(logo_image,layout.logo_rect.width,layout.logo_rect.height,False)
    schedule_image.alpha_composite(logo_image_scaled,layout.logo_rect.top_left)


    ########################################### PLACE BOXES ###########################################################

    box_image_scaled = Image.open(streamer_base_path+"box_scaled.png")
    jump = layout.schedule_rect.height/7

    dateWeekdayNames = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

    today = datetime.date.today()

    myFont = ImageFont.truetype(streamer_base_path+'font.ttf', 40)

    min_name_size = None 
    min_date_size = None 
    min_time_size = None 

    for i in range(7):
        date = today + datetime.timedelta(i) 
        month = date.month 
        day = date.day

        stream_data = ""
        stream_time = ""
        time_zone = ""

        for stream in streams:
            stream_month = stream.unixts.month
            stream_day = stream.unixts.day
            
            if month == stream_month and day == stream_day:
                stream_data = stream.name
                stream_time = stream.unixts.astimezone(pytz.timezone("America/Chicago")).time().strftime("%I:%M %p")
                time_zone = pytz.timezone("America/Chicago").tzname(stream.unixts)

        if stream_data == "":
            stream_data = "N/A"

        weekday = dateWeekdayNames[date.weekday()]

        date_font = get_correct_size(streamer_base_path,f"{month}/{day}\n{weekday}",layout.date_rect.width,layout.date_rect.height)
        dfs = date_font.size

        if(min_date_size == None or dfs < min_date_size):
            min_date_size = dfs

        if stream_time != "" and stream_time != None:
            stream_time_plus_zone = stream_time + "\n" + time_zone

            print(stream_time_plus_zone)

            time_font = get_correct_size(streamer_base_path,stream_time_plus_zone,layout.time_rect.width,layout.time_rect.height)
            tfs = time_font.size

            if(min_time_size == None or tfs < min_time_size):
                min_time_size = tfs

        day_font = get_correct_size(streamer_base_path,f"{stream_data}",layout.name_rect.width,layout.name_rect.height)
        dfss = day_font.size

        if(min_name_size == None or dfss < min_name_size):
            min_name_size = dfss


    no_time_size = get_correct_size(streamer_base_path,"N/A",layout.time_rect.width,layout.time_rect.height)
    name_font = ImageFont.truetype(streamer_base_path+'font.ttf', min_name_size)
    time_font = ImageFont.truetype(streamer_base_path+'font.ttf', min_time_size)
    date_font = ImageFont.truetype(streamer_base_path+'font.ttf', min_date_size)

    font_color_bad = layout.font_color

    font_color = (font_color_bad[0], font_color_bad[1], font_color_bad[2])


    for i in range(7):
        # l/r won't change
        # up and down will
        x = layout.schedule_rect.top_left[0]
        y = int(layout.schedule_rect.top_left[1] + jump*i)

        schedule_image.alpha_composite(box_image_scaled,(x,y))

        date = today + datetime.timedelta(i) 
        month = date.month 
        day = date.day

        stream_data = ""
        stream_time = ""
        time_zone = ""

        for stream in streams:
            stream_month = stream.unixts.month
            stream_day = stream.unixts.day
            
            if month == stream_month and day == stream_day:
                stream_data = stream.name
                stream_time = stream.unixts.astimezone(pytz.timezone("America/Chicago")).time().strftime("%I:%M %p")
                time_zone = pytz.timezone("America/Chicago").tzname(stream.unixts)

        if stream_data == "":
            stream_data = "N/A"

        weekday = dateWeekdayNames[date.weekday()]


        I1 = ImageDraw.Draw(schedule_image)

        ########################################################### DATE ###################################################################################


        text_date_bbox = date_font.getbbox(f"{month}/{day}")

        date_text_height = text_date_bbox[3] - text_date_bbox[1]
        date_text_width = text_date_bbox[2] - text_date_bbox[0]


        I1.text(((x+layout.date_rect.top_left[0]+(layout.date_rect.width//2-date_text_width//2)), y+layout.date_rect.top_left[1])   ,f"{month}/{day}", font=date_font, fill=font_color,anchor="lt")

        text_weekday_zone_bbox = date_font.getbbox(weekday)

        time_weekday_zone_height = text_weekday_zone_bbox[3] - text_weekday_zone_bbox[1]
        time_weekday_zone_width = text_weekday_zone_bbox[2] - text_weekday_zone_bbox[0]

        I1.text(((x+layout.date_rect.top_left[0]+(layout.date_rect.width//2-time_weekday_zone_width//2)), y+layout.date_rect.top_left[1]+(layout.date_rect.height//2)),f"{weekday}", font=date_font, fill=font_color,anchor="lt") 

        ########################################################### stream_time ###################################################################################
        if stream_time == "":
            stream_time_plus_zone = "N/A"
            stream_time = "N/A"

            text_time_bbox = no_time_size.getbbox(stream_time)

            time_text_height = text_time_bbox[3] - text_time_bbox[1]
            time_text_width = text_time_bbox[2] - text_time_bbox[0]

            I1.text(((x+layout.time_rect.top_left[0]+(layout.time_rect.width//2-time_text_width//2)), y+layout.time_rect.top_left[1]+(layout.time_rect.height//2-time_text_height//2))  ,stream_time, font=no_time_size, fill=font_color,anchor="lt")

        else:
            stream_time_plus_zone = stream_time + "\n" + time_zone

            text_time_bbox = time_font.getbbox(stream_time)

            time_text_height = text_time_bbox[3] - text_time_bbox[1]
            time_text_width = text_time_bbox[2] - text_time_bbox[0]


            text_time_zone_bbox = time_font.getbbox(time_zone)

            time_text_zone_height = text_time_zone_bbox[3] - text_time_zone_bbox[1]
            time_text_zone_width = text_time_zone_bbox[2] - text_time_zone_bbox[0]


            I1.text(((x+layout.time_rect.top_left[0]+(layout.time_rect.width//2-time_text_width//2)), y+layout.time_rect.top_left[1])   ,stream_time, font=time_font, fill=font_color,anchor="lt")
            I1.text(((x+layout.time_rect.top_left[0]+(layout.time_rect.width//2-time_text_zone_width//2)), y+layout.time_rect.top_left[1]+(layout.time_rect.height//2))   ,time_zone, font=time_font, fill=font_color,anchor="lt")

        ########################################################### stream name ###################################################################################


        text_name_bbox = name_font.getbbox(f"{stream_data}")

        
        name_text_height = abs(text_name_bbox[3] - text_name_bbox[1])
        name_text_width = abs(text_name_bbox[2] - text_name_bbox[0])

        name_text_length = name_font.getlength(f"{stream_data}")

        I1.text(((x+layout.name_rect.top_left[0]+(layout.name_rect.width//2-name_text_width//2)), y+layout.name_rect.top_left[1]+(layout.name_rect.height/2-name_text_height/2))   ,f"{stream_data}", font=name_font, fill=font_color,anchor="lt")




    schedule_image.save(streamer_base_path+"schedule.png")