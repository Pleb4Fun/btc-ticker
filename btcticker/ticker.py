import math
import time
from PIL import Image, ImageOps
from PIL import ImageFont
from PIL import ImageDraw
import logging
from babel import numbers
from .mempool import *
from blockchain import statistics
from .price import *
from .chart import *
from .config import Config
import os
from datetime import datetime, timedelta


class Ticker():
    def __init__(self, config: Config):
        self.config = config
        self.height = config.main.display_height_pixels
        self.width = config.main.display_width_pixels
        self.fiat = config.main.fiat
        self.orientation = config.main.orientation
        self.inverted = config.main.inverted
        self.mempool = Mempool()
        self.price = Price(fiat=self.fiat, days_ago=1)
        
        self.image = Image.new('L', (self.width, self.height), 255)
        
        self.fontdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'fonts')
        self.fonthiddenprice = ImageFont.truetype(os.path.join(self.fontdir,config.fonts.fonthiddenprice), config.fonts.fonthiddenpricesize)
        self.font = ImageFont.truetype(os.path.join(self.fontdir,config.fonts.font), config.fonts.font_size)

        self.font_price = ImageFont.truetype(os.path.join(self.fontdir,config.fonts.font_price), config.fonts.font_price_size)
        self.font_height = ImageFont.truetype(os.path.join(self.fontdir,config.fonts.font_height),config.fonts.font_height_size)
        self.font_date = ImageFont.truetype(os.path.join(self.fontdir,config.fonts.font_date),config.fonts.font_date_size)
        
        
    def buildFont(self, font_name, font_size):
        return ImageFont.truetype(os.path.join(self.fontdir, font_name), font_size)

    def setDaysAgo(self, days_ago):
        self.price.setDaysAgo(days_ago)

    def drawText(self, x, y, text, font, anchor="la"):
        w, h = self.draw.textsize(text, font=font)
        #start_x, start_y, end_x, end_y =self.draw.textbbox((x,y),text,font=font, anchor=anchor)
        #w = end_x - start_x
        #h = end_y - start_y        
        self.draw.text((x,y),text,font=font,fill = 0, anchor=anchor)
        return w, h

    def drawTextMax(self, x, y, max_w, max_h, text, font_name, start_font_size=20, anchor="la"):
        font_size = start_font_size - 1
        h = 0
        w = 0
        while h < max_h and w < max_w: 
            font_size += 1
            font = ImageFont.truetype(os.path.join(self.fontdir,font_name), font_size)
            start_x, start_y, end_x, end_y =self.draw.textbbox((x,y),text,font=font, anchor=anchor)
            w = end_x - start_x
            h = end_y - start_y
        font_size -= 1
        font = ImageFont.truetype(os.path.join(self.fontdir,font_name), font_size)
        #start_x, start_y, end_x, end_y =self.draw.textbbox((x,y),text,font=font, anchor=anchor)
        #w = end_x - start_x
        #h = end_y - start_y
        w, h = self.draw.textsize(text, font=font)
        self.draw.text((x,y), text, font=font,fill = 0, anchor=anchor)
        return w, h, font_size

    def update(self, mode="fiat", layout="all", mirror=True):
        self.mempool.refresh()
        self.price.refresh()

        symbolstring=numbers.get_currency_symbol(self.fiat.upper(), locale="en")

        mempool = self.mempool.getData()
        current_price = self.price.price
        pricestack = self.price.timeseriesstack

    
        pricechange = self.price.getPriceChange()
        pricenowstring = self.price.getPriceNow()
        
        stats = statistics.get()
        last_retarget = stats.next_retarget - 2016
        
        last_timestamp = mempool["rawblocks"][0]["timestamp"]
        last_height = mempool["rawblocks"][0]["height"]
        last_retarget_blocks = self.mempool.getBlocks(start_height=last_retarget)
        last_retarget_timestamp = last_retarget_blocks[0]["timestamp"]
        remaining_blocks = 2016 - (last_height - last_retarget_blocks[0]["height"])
        difficulty_epoch_duration = stats.minutes_between_blocks * 60 * remaining_blocks + (last_timestamp - last_retarget_timestamp)
        retarget_mult = 14*24*60*60 / difficulty_epoch_duration
        retarget_timestamp = difficulty_epoch_duration + last_retarget_timestamp
        retarget_date = datetime.fromtimestamp(retarget_timestamp)
        
        fee_str = '%.1f-%.1f-%.1f-%.1f-%.1f-%.1f-%.1f'
        #fee_str = 'fee %.0f %.0f %.0f %.0f %.0f %.0f %.0f'
        fee_short_str = '%.1f-%.1f-%.1f'
        #fee_short_str = 'fee %.0f %.0f %.0f'
    
        self.image = Image.new('L', (self.width, self.height), 255)    # 255: clear the image with white
        self.draw = ImageDraw.Draw(self.image)
        minFee = mempool["minFee"]
        medianFee = mempool["medianFee"]
        maxFee = mempool["maxFee"]
        purgingFee = mempool["purgingFee"]
        # meanTimeDiff = mempool["meanTimeDiff"]
        meanTimeDiff = stats.minutes_between_blocks * 60
        t_min = meanTimeDiff // 60
        t_sec = meanTimeDiff % 60
        blocks = math.ceil(mempool["vsize"] / 1e6)
        count = mempool["count"]
        #draw.text((5,2),'%d - %d - %s' % (mempool["height"], blocks, str(time.strftime("%H:%M"))),font =font_height,fill = 0
        if layout == "big":
            if mode == "fiat":
                pos_y = 0
                w, h = self.drawText(5, pos_y, '%d - %d:%d - %s' % (mempool["height"], t_min, t_sec, str(time.strftime("%H:%M"))), self.font_height)
                pos_y += h
                image_y = pos_y
                price_parts = pricenowstring.split(",")
                
                w, h, font_size = self.drawTextMax(5, 5, 260, (176-pos_y-10)/2, price_parts[0], self.config.fonts.font_horizontalbig)
                self.drawText(263, 175, price_parts[1], self.buildFont(self.config.fonts.font_horizontalbig, font_size), anchor="rs")
                self.drawText(5, 100, symbolstring, self.buildFont(self.config.fonts.font_horizontalbig, font_size - 25))
            elif mode == "height" or mode == "newblock":
                pos_y = 0
                w, h = self.drawText(5, pos_y, '%s - %d:%d - %s' % (symbolstring+pricenowstring, t_min, t_sec, str(time.strftime("%H:%M"))), self.font_height)
                pos_y += h
                image_y = pos_y
                price_parts = pricenowstring.split(",")
                                
                w, h, font_size = self.drawTextMax(5, 5, 260, (176-pos_y-10)/2, str(mempool["height"])[:3], self.config.fonts.font_horizontalbig)
                self.drawText(263, 175, str(mempool["height"])[3:], self.buildFont(self.config.fonts.font_horizontalbig, font_size), anchor="rs")

            elif mode == "satfiat":
                pos_y = 0
                w, h = self.drawText(5, pos_y, '%d - %d:%d - %s' % (mempool["height"], t_min, t_sec, str(time.strftime("%H:%M"))), self.font_height)
                pos_y += h
                image_y = pos_y
                w, h = self.drawText(5, pos_y, fee_short_str % (minFee[0], minFee[1], minFee[2]), self.font_date)
                pos_y += h
                price_parts = pricenowstring.split(",")
                w, h = self.drawText(5, pos_y, symbolstring+pricenowstring, self.font_price)
                pos_y += h
                self.drawTextMax(263, 175, 264 - w, 176-pos_y, '%.0f' % (current_price["sat_fiat"]), self.config.fonts.font_horizontalbig, anchor="rs")
                self.drawText(5, 119, "sat", self.font_price)
                self.drawText(5, 141, "/%s" % symbolstring, self.font_price)                
                
            elif mode == "usd":
                pos_y = 0
                w, h = self.drawText(5,pos_y, '%d - %d:%d - %s' % (mempool["height"], t_min, t_sec, str(time.strftime("%H:%M"))), self.font_height)
                pos_y += h
                image_y = pos_y
                price_parts = format(int(current_price["usd"]), ",").split(",")
                
                w, h, font_size = self.drawTextMax(5, 5, 260, (176-pos_y-10)/2, price_parts[0], self.config.fonts.font_horizontalbig)
                pos_y += h
                self.drawText(263, 175, price_parts[1], self.buildFont(self.config.fonts.font_horizontalbig, font_size), anchor="rs")
                
                self.drawText(5, 100, "$", self.buildFont(self.config.fonts.font_horizontalbig, font_size - 25))
                
                
            if mode != "newblock" and mode != "height":
               
                spark_image = makeSpark(pricestack, figsize=(7,3))
                w, h = spark_image.size
                self.image.paste(spark_image ,(150, image_y))                
                
                self.drawText(170, image_y + h, str(self.price.days_ago)+"day : "+pricechange, self.font_date)                
        elif self.config.main.fiat != "usd" and layout != "no_usd":
            if mode == "fiat":
                pos_y = 0
                w, h = self.drawText(5, pos_y, '%d - %d:%d - %s' % (mempool["height"], t_min, t_sec, str(time.strftime("%H:%M"))), self.font_height)
                pos_y += h
                #self.drawText(5, 25, 'fee %.0f|%.1f|%.1f|%.1f|%.1f|%.1f|%.1f' % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]), self.font_date)
                w, h = self.drawText(5, pos_y, fee_str % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]), self.font_date)
                pos_y += h
                image_y = pos_y
                w, h = self.drawText(5, pos_y, '$%.0f' % current_price["usd"], self.font_price)
                pos_y += h
                #draw.text((5,67),'%.1f oz' % current_price["gold"],font =font_price,fill = 0)
                w, h = self.drawText(5, pos_y, '%.0f sat/$' % (current_price["sat_usd"]), self.font_price)
                pos_y += h
                w, h = self.drawText(5, pos_y, '%.0f sat/%s' % (current_price["sat_fiat"], symbolstring), self.font_price)
                pos_y += h
                w, h = self.drawText(5, 130, symbolstring, self.font_price)
                self.drawTextMax(263, 175, 264 - w, 176-pos_y, pricenowstring.replace(",", ""), self.config.fonts.font_horizontalblock, anchor="rs")
            elif mode == "height":
                pos_y = 0
                w, h = self.drawText(5, pos_y, '%s - %d:%d - %s' % (symbolstring+pricenowstring, t_min, t_sec, str(time.strftime("%H:%M"))), self.font_height)
                pos_y += h
                w, h = self.drawText(5, pos_y, fee_str % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]), self.font_date)
                pos_y += h
                image_y = pos_y
                w, h = self.drawText(5, pos_y, '$%.0f' % current_price["usd"], self.font_price)
                pos_y += h
                w, h = self.drawText(5, pos_y, '%.0f sat/$' % (current_price["sat_usd"]), self.font_price)
                pos_y += h
                w, h = self.drawText(5, pos_y, '%.0f sat/%s' % (current_price["sat_fiat"], symbolstring), self.font_price)
                pos_y += h
                self.drawTextMax(263, 175, 263, 176-pos_y, str(mempool["height"]), self.config.fonts.font_horizontalblock, anchor="rs")
                #draw.text((5,67),'%.1f oz' % current_price["gold"],font =font_price,fill = 0)       
            elif mode == "satfiat":
                pos_y = 0
                w, h = self.drawText(5, pos_y, '%d - %d:%d - %s' % (mempool["height"], t_min, t_sec, str(time.strftime("%H:%M"))), self.font_height)
                pos_y += h
                w, h = self.drawText(5, pos_y, fee_str % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]), self.font_date)
                pos_y += h
                image_y = pos_y
                w, h = self.drawText(5, pos_y, '$%.0f' % current_price["usd"], self.font_price)
                pos_y += h
                w, h = self.drawText(5, pos_y, '%.0f sat/$' % (current_price["sat_usd"]), self.font_price)
                pos_y += h
                w, h = self.drawText(5, pos_y, symbolstring+pricenowstring, self.font_price)
                pos_y += h
                # draw.text((5,67),'%.1f oz' % current_price["gold"],font =font_price,fill = 0)
                w, h = self.drawText(5, 119, "sat", self.font_price)
                self.drawText(5, 141, "/%s" % symbolstring, self.font_price)
                self.drawTextMax(263, 175, 264 - w, 176-pos_y, '%.0f' % (current_price["sat_fiat"]), self.config.fonts.font_horizontalblock, anchor="rs")
                
                
            elif mode == "usd":
                pos_y = 0
                w, h = self.drawText(5, pos_y, '%d - %d:%d - %s' % (mempool["height"], t_min, t_sec, str(time.strftime("%H:%M"))), self.font_height)
                pos_y += h
                w, h = self.drawText(5, pos_y, fee_str % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]), self.font_date)
                pos_y += h
                image_y = pos_y
                w, h = self.drawText(5, pos_y, symbolstring+pricenowstring, self.font_price)
                pos_y += h
                # draw.text((5,67),'%.1f oz' % current_price["gold"],font =font_price,fill = 0)
                w, h = self.drawText(5, pos_y, '%.0f sat/$' % (current_price["sat_usd"]), self.font_price)
                pos_y += h
                w, h = self.drawText(5, pos_y, '%.0f sat/%s' % (current_price["sat_fiat"], symbolstring), self.font_price)
                pos_y += h
                w, h = self.drawText(5, 130, '$', self.font_price)          
                self.drawTextMax(263, 175, 264 - w, 176-pos_y, format(int(current_price["usd"]), ""), self.config.fonts.font_horizontalblock, anchor="rs")
                
            elif mode == "newblock":
                pos_y = 0
                w, h = self.drawText(5, pos_y, '%s - %d:%d - %s' % (symbolstring+pricenowstring, t_min, t_sec, str(time.strftime("%H:%M"))), self.font_height)
                pos_y += h
                w, h = self.drawText(5, pos_y, fee_str % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]), self.font_date)
                pos_y += h
                image_y = pos_y
                w, h = self.drawText(5, pos_y, '%d blks %d txs' % (blocks, count), self.font_price)
                pos_y += h
                # draw.text((5,25),'nextfee %.1f - %.1f - %.1f' % (minFee[0], medianFee[0], maxFee[0]),font =font_date,fill = 0)
                # draw.text((5,67),'retarget in %d blks' % remaining_blocks,font =font_price,fill = 0)
                #draw.text((5,67),'%.0f sat/%s' % (current_price["sat_fiat"], symbolstring),font =font_price,fill = 0)
                w, h = self.drawText(5, pos_y, '%d blk %.1f%% %s' % (remaining_blocks, (retarget_mult * 100 - 100), retarget_date.strftime("%d.%b%H:%M")), self.font_price)
                pos_y += h
                self.drawTextMax(263, 175, 264, 176-pos_y, str(mempool["height"]), self.config.fonts.font_horizontalblock, anchor="rs")
                
            if mode != "newblock":
                spark_image = makeSpark(pricestack)
                w, h = spark_image.size
                self.image.paste(spark_image ,(100, image_y))                
                if mode != "satfiat":
                    self.drawText(130, image_y + h, str(self.price.days_ago)+"day : "+pricechange, self.font_date)
                             
        else:
            
            if mode == "fiat":
                pos_y = 0
                w, h = self.drawText(5, pos_y, '%d - %d:%d - %s' % (mempool["height"], t_min, t_sec, str(time.strftime("%H:%M"))), self.font_height)
                pos_y += h
                w, h = self.drawText(5, pos_y, fee_str % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]), self.font_date)
                pos_y += h
                image_y = pos_y
                w, h = self.drawText(5, pos_y, '%.0f sat/%s' % (current_price["sat_fiat"], symbolstring), self.font_price)
                pos_y += h
                w, h = self.drawText(5, 130, symbolstring, self.font_price)
                self.drawTextMax(263, 175, 264 - w, 176-pos_y, pricenowstring.replace(",", ""), self.config.fonts.font_horizontalblock, anchor="rs")
            elif mode == "height":
                pos_y = 0
                w, h = self.drawText(5, pos_y, '%s - %d:%d - %s' % (symbolstring+pricenowstring, t_min, t_sec, str(time.strftime("%H:%M"))), self.font_height)
                pos_y += h
                w, h = self.drawText(5, pos_y, fee_str % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]), self.font_date)
                pos_y += h
                image_y = pos_y
                w, h = self.drawText(5, pos_y, '%.0f sat/%s' % (current_price["sat_fiat"], symbolstring), self.font_price)
                pos_y += h
                self.drawTextMax(263, 175, 263, 176-pos_y, str(mempool["height"]), self.config.fonts.font_horizontalblock, anchor="rs")
                #draw.text((5,67),'%.1f oz' % current_price["gold"],font =font_price,fill = 0)       
            elif mode == "satfiat":
                pos_y = 0
                w, h = self.drawText(5, pos_y, '%d - %d:%d - %s' % (mempool["height"], t_min, t_sec, str(time.strftime("%H:%M"))), self.font_height)
                pos_y += h
                w, h = self.drawText(5, pos_y, fee_str % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]), self.font_date)
                pos_y += h
                image_y = pos_y
                w, h = self.drawText(5, pos_y, symbolstring+pricenowstring, self.font_price)
                pos_y += h
                # draw.text((5,67),'%.1f oz' % current_price["gold"],font =font_price,fill = 0)
                w, h = self.drawText(5, 119, "sat", self.font_price)
                self.drawText(5, 141, "/%s" % symbolstring, self.font_price) 
                self.drawTextMax(263, 175, 264 - w, 176-pos_y, '%.0f' % (current_price["sat_fiat"]), self.config.fonts.font_horizontalblock, anchor="rs")
            elif mode == "usd":
                pos_y = 0
                w, h = self.drawText(5, pos_y, '%d - %d:%d - %s' % (mempool["height"], t_min, t_sec, str(time.strftime("%H:%M"))), self.font_height)
                pos_y += h
                w, h = self.drawText(5, pos_y, fee_str % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]), self.font_date)
                pos_y += h
                image_y = pos_y
                w, h = self.drawText(5, pos_y, symbolstring+pricenowstring, self.font_price)
                pos_y += h
                # draw.text((5,67),'%.1f oz' % current_price["gold"],font =font_price,fill = 0)
                w, h = self.drawText(5, pos_y, '%.0f sat/$' % (current_price["sat_usd"]), self.font_price)
                pos_y += h
                # self.drawText(5, 89, '%.0f sat/%s' % (current_price["sat_fiat"], symbolstring), self.font_price)
                w, h = self.drawText(5, 130, '$', self.font_price)
                self.drawTextMax(263, 175, 264 - w, 176-pos_y, format(int(current_price["usd"]), ""), self.config.fonts.font_horizontalblock, anchor="rs")
               
            elif mode == "newblock":
                pos_y = 0
                w, h = self.drawText(5, pos_y, '%s - %d:%d - %s' % (symbolstring+pricenowstring, t_min, t_sec, str(time.strftime("%H:%M"))), self.font_height)
                pos_y += h
                w, h = self.drawText(5, pos_y, fee_str % (minFee[0], minFee[1], minFee[2], minFee[3], minFee[4], minFee[5], minFee[6]), self.font_date)
                pos_y += h
                image_y = pos_y
                w, h = self.drawText(5, pos_y, '%d blks %d txs' % (blocks, count), self.font_price)
                pos_y += h
                # draw.text((5,25),'nextfee %.1f - %.1f - %.1f' % (minFee[0], medianFee[0], maxFee[0]),font =font_date,fill = 0)
                # draw.text((5,67),'retarget in %d blks' % remaining_blocks,font =font_price,fill = 0)
                #draw.text((5,67),'%.0f sat/%s' % (current_price["sat_fiat"], symbolstring),font =font_price,fill = 0)
                w, h = self.drawText(5, 67, '%d blk %.1f%% %s' % (remaining_blocks, (retarget_mult * 100 - 100), retarget_date.strftime("%d.%b%H:%M")), self.font_price)
                pos_y += h
                self.drawTextMax(263, 175, 264, 176-pos_y, str(mempool["height"]), self.config.fonts.font_horizontalblock, anchor="rs")
        
            if mode != "newblock":
                spark_image = makeSpark(pricestack)
                w, h = spark_image.size
                self.image.paste(spark_image ,(100, image_y))
                self.drawText(130, image_y + h, str(self.price.days_ago)+"day : "+pricechange, self.font_date)
                
        #draw.text((145,2),str(time.strftime("%H:%M %d %b")),font =font_date,fill = 0)
        if self.orientation == 270 :
            self.image=self.image.rotate(180, expand=True)
        if mirror:
            self.image = ImageOps.mirror(self.image)    
    
    #   If the display is inverted, invert the image usinng ImageOps        
        if self.inverted:
            self.image = ImageOps.invert(self.image)
    #   Send the image to the screen        

    def show(self):
        
        self.image.show()