import time, vk, sys
import urllib.request
import os, string
import random
import json
import collections
import matplotlib.pyplot
import numpy

class Program:
    """ Main program class """
    def __init__(self):
        self.alphabet = tuple(list(string.ascii_lowercase) + list(string.ascii_uppercase) +
        [str(x) for x in range(0, 10)] + ['@', '.'])  # alphabet (a-z)+(1-9)
        self.tag = None                 # tag for vk user search
        self.coll = None                # collection for Mongo DB
        self.vkapi = None               # vk api kit
        self.list_of_multidialogs = []  # list of user dialogs, received with vk api
        self.list_of_pic_urls = []      # all the urls from certain dialog
        self.users_pool = {}            # users pool, received with vk api search
        self.folder_name = None         # folder, containing upcoming pics
        self.amount_of_data = 1000      # number of people searched
        self.session = vk.Session()     # simple session
        self.json_data = None


    def save_json_data(self):
        try:
            with open('data.json', 'w', encoding='utf-8') as outfile:
                json.dump(self.json_data, outfile, ensure_ascii=False, indent=4)
            print('Данные сохранены')
            return 1
        except Exception:
            print('Невозможно сохранить данные')
            return 0

    def load_json_data(self):
        file = open('data.json', encoding='utf-8')
        self.json_data = json.loads(file.read(), encoding='utf-8')
        pass


    @staticmethod
    def install_vk_api_for_python():
        """Install vk api via pip in system"""

        print("Установка необходимых библиотек...")
        os.startfile('install_libs.bat', 'runas')

    def vk_sign_in(self):
        """Try to sign in in vk api"""

        app_id = 5531757
        print('\n\n**********АВТОРИЗАЦИЯ**********\n\n')
        if (self.json_data['auth_info']['login'] and self.json_data['auth_info']['password'] and
                self.json_data['auth_info']['login_key'] and self.json_data['auth_info']['password_key']):
            user_login = self.decrypt(self.json_data['auth_info']['login'], self.json_data['auth_info']['login_key'])
            user_password = self.decrypt(self.json_data['auth_info']['password'], self.json_data['auth_info']['password_key'])
        else:
            user_login = input('Введите имя пользователя (e-mail): ')
            user_password = input('Введите пароль: ')
            print("Желаете сохранить логин/пароль? (y/n)")
            while True:
                desision = input();
                if desision == 'y':
                    enc_login = self.encrypt(user_login)
                    enc_password = self.encrypt(user_password)
                    self.json_data['auth_info'] = {'login': enc_login[0],
                                                   'password': enc_password[0],
                                                   'login_key': enc_login[1],
                                                   'password_key': enc_password[1]}
                    self.save_json_data()
                    break
                elif desision == 'n':
                    break


        print('Создание сессии, ожидайте...')
        self.session = vk.AuthSession(app_id=app_id, user_login=user_login, user_password=user_password,
                                      scope="wall, messages")
        print('Сессия создана...')
        print('Подключение к VK api...')
        self.vkapi = vk.API(self.session, timeout=300)
        print('Подключено...\n')


    def vk_token_sing_in(self, token=''):
        try:
            self.session.user_password
        except Exception:
            print('Создание сессии...')
            self.session = vk.Session(access_token=token)
            self.vkapi = vk.API(self.session)
            print('Сессия создана...')
            print('Подключение к VK api...')
            self.vkapi = vk.API(self.session, timeout=300)
            print('Подключено...\n')

    def encrypt(self, string):
        result = ''
        decryption_key = ''
        for letter in str(string):
            shift = random.randint(1, 9)
            new_index = self.alphabet.index(letter) + shift
            if new_index >= len(self.alphabet):
                new_index -= len(self.alphabet)
            result += self.alphabet[new_index]
            decryption_key += str(shift)
        return (result, decryption_key)

    def decrypt(self, string, dec_key):
        result = ''
        decryption_key = dec_key;
        iter = 0
        for letter in str(string):
            shift = int(decryption_key[iter])
            iter += 1
            original_index = self.alphabet.index(letter)-shift
            if original_index < 0:
                original_index += len(self.alphabet)
            result += self.alphabet[original_index]
        return result

    def show_dialogs(self, print_d=True):
        dialogs = self.vkapi.messages.getDialogs(count=200)[1:]
        help_var = 1
        for dialog in dialogs:
            if 'users_count' in dialog:
                # admin_id, date, users_count
                if print_d:
                    print("%d) %s" % (help_var, dialog['title']))
                    print("   Кол-во участников: " + str(dialog['users_count']))
                    hey = self.vkapi.users.get(user_ids=dialog['admin_id'])[0]
                    print("   Создатель: " + hey['first_name'] + ' ' + hey['last_name'])

                
            elif int(dialog['uid']) > 0:
                user = self.vkapi.users.get(user_ids=dialog['uid'])[0]
                if print_d:
                    print("%d) %s %s" % (help_var, user['first_name'], user['last_name']))

            self.list_of_multidialogs.append(dialog)
            help_var += 1
            time.sleep(0.33)


    def select_program(self):
        """Allow user select base program scenario"""

        path_data = self.json_data # Deserialize json
        print('        '+path_data['title'] + '\n\n    ' + path_data['desc'] + '\n\n' +
        path_data['path']['desc'])  # Print title
        for option in path_data['path']['options']:         # Print list of functions
            print(str(option['num'])+'. '+option['desc'])
        scenario = input()
        if scenario == '0':
            self.install_vk_api_for_python()
        elif scenario == '1':
            self.vk_sign_in()
            self.download_pics_from_dialogs()
        elif scenario == '2':
            self.vk_sign_in()
            self.tag = input('По какому тегу будем искать людей? (0 для отмены)\n')
            if self.tag != '0':
                self.get_users_pool()
                self.get_friends_numbers()
            else:
                self.tag = None
        elif scenario == '3':
            counter = self.count_ffn()
            self.check_for_build_plot(counter)
        elif scenario == '4':
            self.vk_token_sing_in()
            self.find_most_popular()
        else:
            print('Ошибка ввода, попробуйте еще раз')
            time.sleep(0.5)
            self.select_program()
        print('Возвращаемся в главное меню...')
        time.sleep(1)
        self.select_program()

    def check_for_build_plot(self, counter):
        inp = input("Построить график?(да/нет)\n\n").lower()
        if inp == 'да':
            self.build_plot(counter)
        elif inp == 'нет':
            pass
        else:
            print("Ошибка ввода, попробуйте еще раз")
            self.check_for_build_plot()

    def download_pics_from_dialogs(self):
        scenario = input('Выберите режим:\n1) Скачать картинки из определенного диалога\n'
                                            '2) Скачать все картинки из всех диалогов\n'
                                            '3) Назад\n')
        if scenario == '1':
            print('\n\nНачинаю подгрузку диалогов...\n\n')
            self.show_dialogs()
            while True:
                print("Из какого диалога будем скачивать фотографии? (Введите 'b', чтобы вернуться)")
                input_number = input()

                input_number = int(input_number)
                if 0 < input_number < len(self.list_of_multidialogs):
                    self.get_dialog_data(self.list_of_multidialogs[input_number - 1])
                    self.ask_for_download()


        elif scenario == '2':
            print('\n\nНачинаю подгрузку диалогов...\n\n')
            self.show_dialogs(print_d=False)
            i = 0
            for dialog in self.list_of_multidialogs:
                i += 1
                print('Загружаю ' + str(i) + ' диалог', end='', flush=True)
                self.get_dialog_data(dialog)
                print();
                time.sleep(0.33)    # Delay for not overloading vk api
            self.ask_for_download()
        elif scenario == '3':
            self.select_program()
        else:
            print('Ошибка ввода, попробуйте еще раз')
            self.download_pics_from_dialogs()

    def find_most_popular(self):
        list_of_popularity = []
        total_user_search = 350000000
        slice = 1000
        c_u = 1
        for user_id in random.sample(range(total_user_search), slice):
            success = False
            while not success:
                try:
                    dict_subs = self.vkapi.users.getSubscriptions(user_id=user_id)
                    success = True
                except Exception:
                    print('error')
            time.sleep(0.33)
            for subed_user_id in dict_subs['users']['items']:
                exist = False
                for element in list_of_popularity:
                    if element['id'] == subed_user_id:
                        element['counter'] += 1
                        exist = True
                if not exist:
                    list_of_popularity.append({'id': subed_user_id, 'counter': 1})
            print('Обработано', c_u, 'пользователей из', slice)
            c_u += 1
        place = 1
        print('\n\n\n\n\n')
        while len(list_of_popularity) > 0 and place <= 10:
            success = False
            max = 0
            index = 0
            for user in list_of_popularity:
                if user['counter'] > max:
                    max = user['counter']
                    index = list_of_popularity.index(user)
            while not success:
                try:
                    user_data = self.vkapi.users.get(user_ids=list_of_popularity[index]['id'])[0]
                    success = True
                except Exception:
                    print('error')
            print(place, 'место:',user_data['first_name'],user_data['last_name'], 'подписано', list_of_popularity[index]['counter'],'человек')
            time.sleep(0.34)
            list_of_popularity.pop(index)
            place += 1

        pass

    def build_plot(self, counter):
        sutable_list = []
        total_numbers = 0
        for element in counter:
            sutable_list.append(element[1])
            total_numbers += element[1]
        benf_list = [30.1, 17.6, 12.5, 9.7, 7.9, 6.7, 5.8, 5.1, 4.6]
        benf_list = [x*total_numbers/100 for x in benf_list]
        width = 0.35
        transparency = 0.3
        num_of_col = numpy.arange(1, 10, 1)
        fig, ax = matplotlib.pyplot.subplots()
        rects1 = ax.bar(num_of_col++width, sutable_list, width, label='Data')
        benf_rects = ax.bar(num_of_col + width*2, benf_list, width, alpha=transparency, color='r',  label='Benford')
        ax.set_xlabel('Number')
        ax.set_ylabel('Amount')
        ax.set_title('Frequency of first number in friends counter appearing')
        ax.set_xticks(num_of_col + width/2)
        ax.set_xticklabels(('1', '2', '3', '4', '5', '6', '7', '8', '9'))
        matplotlib.pyplot.axis([1, 9.99, 0, max(sutable_list)*2])
        matplotlib.pyplot.xticks(num_of_col + width * 1.5, num_of_col)
        matplotlib.pyplot.legend()
        for rect in rects1:
            height = rect.get_height()
            ax.text(rect.get_x() + rect.get_width()/2, 1.05 * height,
                    str(round(height/total_numbers*100, 2))+'%',
                    ha='center', va='bottom', fontsize=10)
        matplotlib.pyplot.show()

    def count_ffn(self):
        sum_of_friends = 0
        num_of_numer = 0
        self.tag = self.json_data['tag']
        print('     Данные по тегу '+self.tag)
        first_numbers = []
        for user in self.json_data['friends']:
            first_numbers.append(int(str(user)[0]))
            sum_of_friends += user
            num_of_numer += 1
        print('Всего значений получено:', num_of_numer)
        counter = collections.Counter(first_numbers).most_common()
        for element in range(1, 10):
            for el in counter:
                if el[0] == element:
                    print(str(el[0])+' встречается ' + str(el[1])+' раз (', round(el[1]/len(first_numbers)*100, 2),'%)', sep='')
        print('В средем у тега (', self.json_data['tag'],') ', round(sum_of_friends/len(self.son_data['friends'])), ' друзей', sep='')
        return counter

    def get_dialog_data(self, dialog, start_from=None, dialog_number=None):
        peer_id = None
        if 'chat_id' in dialog:
            peer_id = 2000000000 + dialog['chat_id']
        elif int(dialog['uid']) > 0:
            peer_id = dialog['uid']

        if not start_from:
            photo_array = self.vkapi.messages.getHistoryAttachments(peer_id=peer_id,
                                                                    media_type='photo', count=200)
        else:
            photo_array = self.vkapi.messages.getHistoryAttachments(peer_id=peer_id,
                                                                    media_type='photo', count=200, start_from=start_from)

        print('.', end='', flush=True)
        if type(photo_array) is dict:
            next_from = photo_array['next_from']
            photo_array.pop("0")
            photo_array.pop("next_from")
            for key in sorted(photo_array.keys()):
                photo = photo_array[key]['photo']
                if photo.get('src_xxbig'):
                    self.list_of_pic_urls.append(photo['src_xxbig'])
                elif photo.get('src_xbig'):
                    self.list_of_pic_urls.append(photo['src_xbig'])
                elif photo.get('src_big'):
                    self.list_of_pic_urls.append(photo['src_big'])
                elif photo.get('src'):
                    self.list_of_pic_urls.append(photo['src'])
                elif photo.get('src_small'):
                    self.list_of_pic_urls.append(photo['src_small'])
            time.sleep(0.4)
            self.get_dialog_data(dialog, next_from, dialog_number=dialog_number)
        else:
            photo_array = photo_array[1:]
            for element in photo_array:
                photo = element['photo']
                if photo.get('src_xxbig'):
                    self.list_of_pic_urls.append(photo['src_xxbig'])
                elif photo.get('src_xbig'):
                    self.list_of_pic_urls.append(photo['src_xbig'])
                elif photo.get('src_big'):
                    self.list_of_pic_urls.append(photo['src_big'])
                elif photo.get('src'):
                    self.list_of_pic_urls.append(photo['src'])
                elif photo.get('src_small'):
                    self.list_of_pic_urls.append(photo['src_small'])
            time.sleep(0.4)

    def get_users_pool(self):
        print('Ищем людей с тегом', self.tag)
        self.users_pool = self.vkapi.users.search(count=self.amount_of_data, q=self.tag, sort=0)
        self.users_pool.pop(0)

    def get_friends_numbers(self):
        self.friends_amount = {'friends':[]}
        total_users = len(self.users_pool)
        current_user_number = 1
        self.friends_amount['tag'] = self.tag
        for user in self.users_pool:
            success = False
            while not success:
                try:
                    user_info = self.vkapi.users.get(user_ids=user['uid'], fields='counters')
                    success = True
                except Exception:
                    print('Ошибка, повтор операции...')
            num = user_info[0]['counters']['friends']
            if num != 0:
                self.friends_amount['friends'].append(user_info[0]['counters']['friends'])
            time.sleep(0.34)
            print('Обработано %d из %d пользователей\n' % (current_user_number, total_users))
            current_user_number+=1
        with open('friends.json', 'w', encoding='utf-8') as f:
            json.dump(self.friends_amount, f, ensure_ascii=False, indent=4)

    def print_number_of_urls(self):
        print("Всего картинок:", len(self.list_of_pic_urls))

    def start_downloading(self):
        help = 1
        if not os.path.isdir('pics\\'+self.folder_name):    # Create folder if not exist
            os.makedirs('pics\\'+self.folder_name)
        i = 0;
        for url in self.list_of_pic_urls:
            print("Получаю картинку " + str(i) + ', url: ' + url)
            i +=1 ;
            try:
                urllib.request.urlretrieve(url, "pics\\"+self.folder_name+'\\'+str(help)+".jpg")
            except Exception:
                print('     Не удалось загрузить картинку')
            help += 1

    def ask_for_download(self):
        self.print_number_of_urls()
        state = input("Хотите начать загрузку %d фотографий? (y/n)\n" % len(self.list_of_pic_urls))
        if state == 'y':
            self.folder_name = input("Введите название папки, куда будут сохранены картинки\n")
            self.start_downloading()
        elif state != 'n':
            self.ask_for_download()

    def main(self):
        program_object.load_json_data()
        program_object.select_program()

program_object = Program()
program_object.main()
