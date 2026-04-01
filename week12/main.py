# https://freesimplegui.readthedocs.io/en/stable/
# pip install FreeSimpleGUI

import FreeSimpleGUI as sg
import random
import re
import glob

# Simple script to read flash cards file and display contents
# Read in file contents
# load chapters for combo box by iterating through lines in file and picking ones with a # at the beginning
def load_chapter_titles(chapters, lines):
    chapters.clear()   # empty out list
    pattern = r'[^,\.:A-Za-z0-9]+'  # define allowable characters
    for line in lines:  # go through file contents
        line = line.strip()
        if line.find('#',0,1) == 0:
            line = line.replace('#','')
            line = re.sub(pattern, ' ', line) # replace any characters other than specified
            line = line.strip() # remove extra white space
            chapters.append(line)

# read all the cards in the chapter
# populates the cards dictionary, using the passed in chapter, from the lines list
def load_cards(cards, chapter, lines):
    cards.clear()
    in_chapter = False
    for line in lines:
        line = line.strip()
        if line.find('#',0,1) == 0:
            pattern = r'[^,\.:A-Za-z0-9]+'
            line = re.sub(pattern, ' ', line)
            if chapter in line: # found chapter looked for
                in_chapter = True
                continue
            elif in_chapter:
                break   # reached end of chapter

        # if already in chapter, continue parsing
        elif in_chapter:
            pattern = r'[^,\.:A-Za-z0-9]+'
            line = re.sub(pattern, ' ', line)
            items = line.split(':')   # add words to dictionary
            if (len(items) == 2):
                cards[items[0]] = items[1] # add card with term the key and definition the value

# select card from chapter
# rnd - boolean, if true selecte a random card
# otherwise - select card indicated by ndx
def choose_card(cards, rnd, ndx = 0):
    count = len(cards) # get number of cards in chapter
    if rnd:
        ndx = random.randint(0, count - 1)  # pick a random card
    else:
        if ndx > count - 1:
            ndx = 0
        elif ndx < 0:
            ndx = count - 1

    keys = list(cards.keys())     # create a list of all the keys
    return tuple((keys[ndx], cards[keys[ndx]], ndx))    # return single card as a tuple of value, definition, and current index

# handles word wrap
def update_display(window, txt):
    txt_len = len(txt)
    lines = 5
    if txt_len > 26:
        lines = int((10 - txt_len / 26) / 2)
    display_text = ""
    for i in range(lines):
        display_text=display_text + '\n'
    display_text = display_text + txt
    window['-text-'].update(display_text)

def loadFiles():
    files = glob.glob("./*.yaml")
    for i in range(len(files)):
        files[i] = files[i].replace('.yaml','')
        index = files[i].rfind('\\') + 1
        if index >= 0:  # if found
            files[i] = files[i][index:]
    return files
def loadData(file):
    # read in yaml file
    with open(file + '.yaml') as f:
        return f.readlines()

# initialize app
def main():
    chapters = [] # list of chapters
    cards = {} # dictionary of cards
    data_files = loadFiles()

    # load first data file by default
    if len(data_files) > 0:
        lines = loadData(data_files[0])

    # load chapters
    load_chapter_titles(chapters, lines)

    # load cards
    load_cards(cards, chapters[0], lines)

    # pick random card
    card = choose_card(cards, True, 0)

    # ui layout
    sg.theme('Dark Green 7')

    layout = [
        # section 1
        [[sg.Combo(chapters, font=('Arial', 16), enable_events=True,
                  default_value=chapters[0], size=(48, 1), key='-CHAPTER-'),

        sg.Combo(data_files, font=('Arial', 16), enable_events=True,
                  default_value=data_files[0], size=(20, 1), key='-FILE-')]],
        # section 2
        [sg.Multiline(size=(35, 10), justification='center', border_width=0, background_color="#0C231E",
                      font=('Courier', 48), no_scrollbar=True, key='-text-')],
        # section 3
        [sg.Checkbox('Random', font=('Arial', 16), default=True, enable_events=True, key="-RND-"),
         sg.Button('Prev', font=('Arial', 16), enable_events=True, key='-PREV-'),
         sg.Button('Show/Hide', font=('Arial', 16), enable_events=True, key='-SHOW-'),
         sg.Button('Next', font=('Arial', 16), enable_events=True, key='-NEXT-')]]

    window = sg.Window('Flashcards', layout, size=(1000, 800), grab_anywhere=False)

    show_def = False

    # event loop
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Cancel'):
            break
        elif event == '-FILE-':
            lines = loadData(values['-FILE-'])
            load_chapter_titles(chapters, lines)
            load_cards(cards, chapters[0], lines)
            card = choose_card(cards, True)
            update_display(window, card[0])
            window['-CHAPTER-'].update(value = chapters[0], values = chapters)
        elif event == '-CHAPTER-':
            load_cards(cards, values['-CHAPTER-'], lines)
            card = choose_card(cards, True)
            update_display(window, card[0])
        elif event == '-NEXT-':
            card = choose_card(cards, values['-RND-'], card[2] + 1)
            update_display(window, card[0])
            show_def = False
        elif event == '-PREV-':
            card = choose_card(cards, values['-RND-'], card[2] - 1)
            update_display(window, card[0])
            show_def = False
        elif event == '-SHOW-':
            show_def = not show_def
            if show_def:
                update_display(window, card[1])
            else:
                update_display(window, card[0])

    window.close()

main()