from tkinter import *
import tkinter.messagebox
from os import listdir
from urllib.request import urlopen
from PIL import Image, ImageTk

root = Tk()

imgs_directory = [f"images//{img_file}" for img_file in listdir("images")]
# img_files = imgs_directory[:10]


# def blit_image(img_file, renders, resize_factor, x, y):
#     load_image = Image.open(img_file)
#     resize = load_image.resize((int(load_image.size[0] * resize_factor), int(load_image.size[1] * resize_factor)))
#     renders.append(ImageTk.PhotoImage(resize))
#     img = Label(root, image=renders[-1])
#     width, height = img.winfo_reqwidth(), img.winfo_reqheight()
#     img.place(x=x, y=y)
#     text = Label(root, text=img_file[8:-4])
#     text.config(font=('arial', 20, 'bold'))
#     text.place(x=x+20, y=y+height)


def blit_page_of_images(root, img_files):
    renders = []
    for i, img_file in enumerate(img_files):
        load_image = Image.open(img_file)
        resize = load_image.resize(((load_image.size[0]*65) // 100, (load_image.size[1]*65) // 100))
        renders.append(ImageTk.PhotoImage(resize))
        img = Label(root, image=renders[-1])
        width, height = img.winfo_reqwidth(), img.winfo_reqheight()
        img.place(x=(i % 5)*(width + 30) + 10, y=(i//5)*(height + 50) + 10)
        text = Label(root, text=img_file[8:-4])
        text.config(font=('arial', 20, 'bold'))
        text.place(x=(i % 5)*(width + 30) + 30, y=(i//5)*(height + 50) + 10 + height)


blit_page_of_images(root, imgs_directory[:10])

root.mainloop()