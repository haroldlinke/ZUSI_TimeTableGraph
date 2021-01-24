from Tkinter import *

def main():

    root = Tk()
    root.geometry("%dx%d+0+0" % (1800,1000))
    cv = Canvas(root)
    vscrollbar = Scrollbar(root, orient=VERTICAL)
    vscrollbar.pack(fill=Y, side=RIGHT)
    vscrollbar.config(command=cv.yview)
    cv.configure(yscrollcommand=vscrollbar.set)
    cv.configure(scrollregion=(0,0, 4000, 50000))      
    cv.pack(side=LEFT, fill=BOTH, expand=TRUE)
    
    mainloop()

main()