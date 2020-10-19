import kivy
kivy.require("1.8.1")
from kivy.uix.button import Label, Button
from kivy.uix.widget import Widget
from kivy.uix.stacklayout import StackLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.lang import Builder
from kivy.app import App
from kivy.uix.popup import Popup

from webdata import UrlReading
from support import Effect, call_control, MultiExpressionButton
# Need to handle back button
class mainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.addbooks()

    def addbooks(self):
        self.books = self.ids["books"]
        i = 0
        for line in open("readerInfo.txt", "r+").readlines():
            try:
                title, url = line.split("  ")
            except ValueError:
                with open("readerInfo.txt","r+") as f:
                    new_f = f.readlines()
                with open("readerInfo.txt", "w+") as n:
                    for line in new_f:
                        if line is not "\n":
                            n.write(line)
                        n.truncate()
                    continue
            self.insertWidget(title, i)
            i+=1

    def insertWidget(self, title, lineNum):
        btn = MultiExpressionButton(
            text = title,
            size_hint = (.33, None),
            text_size = (self.width, None),
        )
        btn.bind(
            on_single_press = (lambda x: wm.readerScreen(lineNum)),
            on_long_press   = (lambda x: wm.inputScreen (lineNum))
        )
        self.books.add_widget(btn)

from support import asList            
class readerScreen(Screen):
    def __init__(self, lineNum, **kwargs):
        super().__init__(**kwargs)
        self.ids["contentScroll"].effect_y = Effect(
            Next = lambda: self.changePage(self.next),
            Prev = lambda: self.changePage(self.prev))
        self._current = None
    @call_control(3)
    def changePage(self, page):
        if page != None:
            self.currentUrl(page)
        else:
            wm.mainScreen()
        self.ids.contentScroll.scroll_y = 1
    def currentUrl(self, value):
        # Using self.lineNum, update that line of the file
        if type(value) == str:
            self._current, self.ids["title"].text, self.next, self.prev, self.ids["content"].text = asList(value)

class inputScreen(Screen):
    def __init__(self, lineNum, **kwargs):
        super().__init__(**kwargs)
        self.nickText = self.ids.nickText
        self.urlText  = self.ids.urlText
        
        if lineNum is not None:
            self.lineNum = lineNum
            with open("readerInfo.txt", "r") as f:
                title, url = f.readlines()[lineNum].split("  ")
            self.nickText.text = title
            self.urlText.text  = url
    def delete(self):
        if self.lineNum is not None:
            with open("readerInfo.txt","r+") as f:
                new_f = f.readlines()
            with open("readerInfo.txt", "w+") as n:
                for line in new_f:
                    if self.urlText.text not in line:
                        n.write(line)
                    n.truncate()
        wm.mainScreen()
    def add(self):
        warning = Popup(title = "Invalid Data",
                 content = Label(text = """ 
                 Data Entered was invalid, look for supported websites and urls
                 None of the textInputs should be empty
                 """), size_hint = (1, 0.5))
        if len(self.nickText.text) != 0 and len(self.urlText.text):
            try:
                asList(self.urlText.text)
                with open("readerInfo.txt", "a+") as f:
                    line = "  ".join([self.nickText.text, self.urlText.text])
                    f.write("\n")
                    f.write(line)
            except ValueError:
                warning.open()
        warning.open()
        wm.mainScreen()



class WindowManager(ScreenManager):
    def readerScreen(self, lineNum):
        with open("readerInfo.txt", "r") as f:
            url = f.readlines()[lineNum].split("  ")[1]
        self.reader = readerScreen(lineNum = lineNum, name = "reader")
        self.switch_to(self.reader, direction = 'left')
        self.reader.currentUrl(url)
    
    def mainScreen(self):
        self.main = mainScreen(name = "Main")
        self.switch_to(self.main, direction = "right")
    
    def inputScreen(self, lineNum = None):
        self.input = inputScreen(lineNum, name = "input")
        self.switch_to(self.input, direction = "left")

    

Builder.load_file("main.kv")
wm = WindowManager()
wm.add_widget(mainScreen(name = "main"))

class main(App):
    def build(self):
        return wm

if __name__ == "__main__":
    app = main()
    app.run()
    