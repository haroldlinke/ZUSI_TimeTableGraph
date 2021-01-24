from tkinter import *

my_window = Tk()

my_frame_in = Frame(my_window)
my_frame_in.grid(row=0, column=0)
my_frame_out = Frame(my_window)
my_frame_out.grid(row=0, column=1)

listbox_events = Listbox(my_frame_in, height='5', selectmode=EXTENDED)
listbox_events.grid(row=0, column=0, padx=10, pady=10)
listbox_events_filtered = Listbox(my_frame_out, height='5', selectmode=EXTENDED)
listbox_events_filtered.grid(row=0, column=2, padx=(0, 10), pady=10)
my_instructions = Label(my_window, text='Use arrow keys to move selected items')
my_instructions.grid(row=1, column=0, columnspan=3, pady=(0, 10))

my_list_events = ['A', 'B', 'C', 'D']

for item in my_list_events:
    listbox_events.insert(END, item)


def move_items(event):
    if event.keysym == 'Right':
        src_list = listbox_events
        dst_list = listbox_events_filtered
    elif event.keysym == 'Left':
        src_list = listbox_events_filtered
        dst_list = listbox_events
    else:
        return

    for _item in src_list.curselection():
        dst_list.insert(END, src_list.get(_item))

    for _item in reversed(src_list.curselection()):
        src_list.delete(_item)


listbox_events.bind('<Right>', move_items)
listbox_events_filtered.bind('<Left>', move_items)


mainloop()