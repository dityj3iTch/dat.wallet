import sys
from kivy.app import App
from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.image import AsyncImage
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.treeview import TreeView, TreeViewLabel
from kivy.uix.popup import Popup
from kivy.uix.listview import ListView, ListItemLabel, ListItemButton
from kivy.adapters.listadapter import ListAdapter
from kivy.core.clipboard import Clipboard

from kivy.config import Config
# golden ratio
Config.set('graphics', 'width', 309)
Config.set('graphics', 'height', 500)
#Config.set('graphics', 'resizable', 0)

from kivy.support import install_twisted_reactor
install_twisted_reactor()
from twisted.internet import reactor

import backend_core
import clipboard

MAX_UINT32 = 4294967295

class RootWidget(BoxLayout):
    pass


class BalanceSection(BoxLayout):

    def __init__(self, backend, **kwargs):
        super(BalanceSection, self).__init__(**kwargs)
        self.backend = backend

        main_layout = BoxLayout(orientation='horizontal')

        # TODO wire up the real amount to a formatter which gets fed here
        main_layout.add_widget(Label(text='1,276.00 mBTC', font_size=28, bold=True))

        self.add_widget(main_layout)

class ReceiveSection(BoxLayout):

    def __init__(self, backend, **kwargs):
        super(ReceiveSection, self).__init__(**kwargs)
        self.backend = backend

        main_layout = BoxLayout(orientation='vertical')

        nextaddress_label = Label(text='click below to copy\nnext receive address',
            size_hint_y=0.5, font_size=20, halign='center')
        main_layout.add_widget(nextaddress_label)

        # TODO wire this text input up to a real address which may change when a transaction to this address occurs
        self.current_address = self.backend.current_address
        shortened_address = self.current_address[:6] + "..."
        nextaddress_input = Button(
            text=shortened_address,
            size_hint_y=0.3,
            font_size=20,
            foreground_color=(1,1,1,1))
        nextaddress_input.bind(on_press=self.copy_address_to_clipboard)
        nextaddress_input.next_address = self.current_address
        main_layout.add_widget(nextaddress_input)

        self.add_widget(main_layout)

    def copy_address_to_clipboard(self, instance):
        address = instance.next_address
        clipboard.copy(address)
        self.show_copied_popup(address)
        print Clipboard.get('UTF8_STRING')

    def show_copied_popup(self, address):
        btnclose = Button(text='Close this popup', size_hint_y=None, height='50sp')
        content = BoxLayout(orientation='vertical')
        row_length = 15
        for i in range(0, len(address), row_length):
            content.add_widget(Label(text=address[i:i + row_length]))
        content.add_widget(btnclose)
        popup = Popup(content=content, title='Copied Address',
                      size_hint=(None, None), size=('300dp', '300dp'))
        btnclose.bind(on_release=popup.dismiss)
        button = Button(text='Open popup', size_hint=(None, None),
                        size=('150sp', '70dp'),
                        on_release=popup.open)
        popup.open()
        col = AnchorLayout()
        col.add_widget(button)
        return col

class SendSection(BoxLayout):

    def __init__(self, backend, **kwargs):
        super(SendSection, self).__init__(**kwargs)
        self.backend = backend

        self.main_layout = BoxLayout(orientation='vertical')

        self.sendaddress = TextInput(hint_text="Enter a payment address", size_hint_y=0.2, font_size=20)
        self.main_layout.add_widget(self.sendaddress)

        self.sendsection = BoxLayout(orientation='horizontal', size_hint_y=0.4)
        self.amount_mbtc = TextInput(text='125', halign='right', font_size=20, padding=(20, 20))
        self.sendsection.add_widget(self.amount_mbtc)
        self.sendsection.add_widget(Label(text='mBTC', halign='left'))
        self.sendbutton = Button(text='Send')
        self.sendbutton.bind(on_press=self.call_send)
        self.sendsection.add_widget(self.sendbutton)

        self.main_layout.add_widget(self.sendsection)

        self.add_widget(self.main_layout)

    def call_send(self, instance):
        toaddress = self.sendaddress.text
        # precision of float() ?
        amount_satoshis = float(self.amount_mbtc.text) * 1e5
        print 'should send', str(amount_satoshis) ,'to address ', toaddress
        # TODO validate address
        # TODO call backend send function


class TranscationSection(BoxLayout):

    def __init__(self, backend, **kwargs):
        super(TranscationSection, self).__init__(**kwargs)       
        self.backend = backend
        self.transactions = [{'value': 'No transactions'}]

        main_layout = BoxLayout(orientation='vertical')

        self.transaction_history = self.make_transaction_widget()
        main_layout.add_widget(self.transaction_history)

        self.add_widget(main_layout)




    def make_transaction_widget(self):
        print 'make_transaction_widget called'
        args_converter = lambda row_index, rec: {'text': str(rec['value']),
                                         'size_hint_y': None,
                                         'height': 25}

        #self.transaction_history = ListView(item_strings=self.get_transactions(0,50))
        print self.transactions
        transaction_history = ListAdapter(data=self.transactions,
            args_converter=args_converter,
            cls=ListItemLabel,
            selection_mode='single',
            allow_empty_selection=False)

        #self.list_view.adapter = transaction_history
        list_view = ListView(adapter=transaction_history)
        return list_view


    def get_transactions(self, start=0, amount=100):
        print self.transactions
        #item_strings=[('row ' + str(index) + ': +500 mBTC sent to 1MNmTP...') for index in range(amount)]
        transaction_strings=[]
        for txhash, tx in self.transactions:
            if s_index != MAX_UINT32:
                transaction_strings.append('+' + tx['value'] + ' satoshis received on ' + tx['address'])
            else:
                transaction_strings.append(tx['value'] + ' satoshis sent from ' + tx['addrdress'])

        print transaction_strings
        return transaction_strings

class MainApp(App):

    def __init__(self, backend):
        super(MainApp, self).   __init__()
        self.backend = backend
        self.transactions = []

    def cb(self, addr, history):
        # print addr, history
        for row in history:
            o_hash, o_index, o_height, value, s_hash, s_index, s_height = row
            if s_index != MAX_UINT32:
                value = -value
            self.transactions.append({'address': addr, 'o_hash': o_hash.encode('hex'), 'o_index': o_index, 'o_height': o_height, 'value': value,
            's_hash': s_hash.encode("hex"), 's_index': s_index, 's_height': s_height})

        #self.trans.transaction_history.add_node(TreeViewLabel(text=str(value) + ' satoshis sent to/from ' + addr))
        self.trans.transactions = self.transactions
        #self.trans.remove_widget(self.trans.transaction_history)
        self.trans.transaction_history = self.trans.make_transaction_widget()
        #self.trans.add_widget(self.trans.transaction_history)

        #print self.transactions

    def build(self):
        root = RootWidget()

        main_layout = BoxLayout(orientation='vertical')
        main_layout.add_widget(BalanceSection(backend=self.backend, size_hint_y=0.4))
        main_layout.add_widget(ReceiveSection(backend=self.backend, size_hint_y=1))
        main_layout.add_widget(SendSection(backend=self.backend, size_hint_y=0.7))
        self.trans = TranscationSection(backend=self.backend, size_hint_y=1)
        main_layout.add_widget(self.trans)

        root.add_widget(main_layout)

        self.backend.update(self.cb)

        return root

if __name__ == '__main__':
    if len(sys.argv) == 1: sys.argv[1:] = ["correct horse battery staple"]
    print "\n".join(sys.argv)

    #import mnemonic
    #seedphrase = mnemonic.mn_decode(sys.argv[1])
    seedphrase = sys.argv[1].encode("hex")
    print seedphrase
    backend = backend_core.Backend(seedphrase)
    MainApp(backend).run()

