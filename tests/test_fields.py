from datetime import datetime, date, time, timedelta
from decimal import Decimal
from uuid import UUID
from django.test import TestCase
from django.core.exceptions import ValidationError
from test_app.models import AllFieldsModel, BigAutoModel
from django_prepared_query import BindParam, NotSupportedLookup


class FieldsTestCase(TestCase):
    def test_auto_field(self):
        qs = AllFieldsModel.objects.filter(id=BindParam('id')).prepare()
        qs.execute(id=5)
        qs.execute(id='5')
        with self.assertRaises(ValidationError):
            qs.execute(id='text')

    def test_big_int(self):
        qs = AllFieldsModel.objects.filter(big_int=BindParam('big_int')).prepare()
        qs.execute(big_int=1234567890)
        qs.execute(big_int='1234567890')
        with self.assertRaises(ValidationError):
            qs.execute(big_int='text')
        with self.assertRaises(ValidationError):
            qs.execute(big_int=12345678901234567890)

    def test_binary(self):
        '''
        Django doesn't validate binary field, so it's just smoke test
        '''
        qs = AllFieldsModel.objects.filter(binary=BindParam('binary')).prepare()
        qs.execute(binary=b'123')
        qs.execute(binary='123')

    def test_boolean(self):
        qs = AllFieldsModel.objects.filter(boolean=BindParam('boolean')).prepare()
        qs.execute(boolean=True)
        with self.assertRaises(ValidationError):
            qs.execute(boolean='true')

    def test_char(self):
        qs = AllFieldsModel.objects.filter(char=BindParam('char')).prepare()
        qs.execute(char='123')
        qs.execute(char=123)
        with self.assertRaises(ValidationError):
            qs.execute(char='1234567890')  # max_length validation

    def test_date(self):
        qs = AllFieldsModel.objects.filter(date=BindParam('date')).prepare()
        qs.execute(date=date(year=2018, month=1, day=1))
        qs.execute(date='2018-01-01')
        with self.assertRaises(ValidationError):
            qs.execute(date=1234567890)
        with self.assertRaises(ValidationError):
            qs.execute(date='1234567890')

    def test_datetime(self):
        qs = AllFieldsModel.objects.filter(datetime=BindParam('datetime')).prepare()
        qs.execute(datetime=datetime(year=2018, month=1, day=1))
        qs.execute(datetime='2018-01-01')
        with self.assertRaises(ValidationError):
            qs.execute(datetime=1234567890)
        with self.assertRaises(ValidationError):
            qs.execute(datetime='1234567890')

    def test_decimal(self):
        d = Decimal('123.12')
        qs = AllFieldsModel.objects.filter(decimal=BindParam('decimal')).prepare()
        qs.execute(decimal=d)
        qs.execute(decimal='123.12')
        qs.execute(decimal=123)
        with self.assertRaises(ValidationError):
            qs.execute(decimal='text')

    def test_duration(self):
        '''
        Django doesn't validate duration field, so it's just smoke test
        '''
        td = timedelta(minutes=1)
        qs = AllFieldsModel.objects.filter(duration=BindParam('duration')).prepare()
        qs.execute(duration=td)
        qs.execute(duration='1 minute')

    def test_email(self):
        qs = AllFieldsModel.objects.filter(email=BindParam('email')).prepare()
        qs.execute(email='some@mail.com')
        with self.assertRaises(ValidationError):
            qs.execute(email='not email')
        with self.assertRaises(ValidationError):
            qs.execute(email=123)

    def test_file(self):
        '''
        Django doesn't validate file field, so it's just smoke test
        '''
        qs = AllFieldsModel.objects.filter(file=BindParam('file')).prepare()
        qs.execute(file='file.txt')

    def test_file_path(self):
        '''
        Django doesn't validate file path field, so it's just smoke test
        '''
        qs = AllFieldsModel.objects.filter(file_path=BindParam('file_path')).prepare()
        qs.execute(file_path='file.txt')

    def test_float(self):
        qs = AllFieldsModel.objects.filter(float=BindParam('float')).prepare()
        qs.execute(float=1.2)
        qs.execute(float='1.2')
        qs.execute(float=1)
        with self.assertRaises(ValidationError):
            qs.execute(float='text')

    def test_image(self):
        '''
        Django doesn't validate image field, so it's just smoke test
        '''
        qs = AllFieldsModel.objects.filter(image=BindParam('image')).prepare()
        qs.execute(image='image.png')

    def test_int(self):
        qs = AllFieldsModel.objects.filter(int=BindParam('int')).prepare()
        qs.execute(int=1)
        qs.execute(int='1')
        with self.assertRaises(ValidationError):
            qs.execute(int=2147483648)
        with self.assertRaises(ValidationError):
            qs.execute(int='text')

    def test_generic_ip(self):
        qs = AllFieldsModel.objects.filter(generic_ip_address=BindParam('ip_address')).prepare()
        qs.execute(ip_address='192.0.2.30')
        qs.execute(ip_address='2a02:42fe::4')
        qs.execute(ip_address='::ffff:192.0.2.0')
        with self.assertRaises(ValidationError):
            qs.execute(ip_address=127001)
        with self.assertRaises(ValidationError):
            qs.execute(ip_address='incorrect ip')

    def test_null_boolean(self):
        qs = AllFieldsModel.objects.filter(null_boolean=BindParam('bool')).prepare()
        qs.execute(bool=True)
        qs.execute(bool=None)
        with self.assertRaises(ValidationError):
            qs.execute(bool='true')

    def test_positive_int(self):
        qs = AllFieldsModel.objects.filter(positive_int=BindParam('int')).prepare()
        qs.execute(int=123)
        qs.execute(int='123')
        with self.assertRaises(ValidationError):
            qs.execute(int=4294967296)
        with self.assertRaises(ValidationError):
            qs.execute(int='text')
        with self.assertRaises(ValidationError):
            qs.execute(int=-5)

    def test_positive_small_int(self):
        qs = AllFieldsModel.objects.filter(positive_small_int=BindParam('int')).prepare()
        qs.execute(int=123)
        qs.execute(int='123')
        with self.assertRaises(ValidationError):
            qs.execute(int=65536)
        with self.assertRaises(ValidationError):
            qs.execute(int='text')
        with self.assertRaises(ValidationError):
            qs.execute(int=-5)

    @staticmethod
    def test_slug():
        '''
        Django doesn't validate slug field, so it's just smoke test
        '''
        qs = AllFieldsModel.objects.filter(slug=BindParam('slug')).prepare()
        qs.execute(slug='why-do-some-websites-add-slugs-to-the-end-of-urls')

    def test_small_int(self):
        qs = AllFieldsModel.objects.filter(small_int=BindParam('int')).prepare()
        qs.execute(int=123)
        qs.execute(int='123')
        with self.assertRaises(ValidationError):
            qs.execute(int=32768)
        with self.assertRaises(ValidationError):
            qs.execute(int='text')

    @staticmethod
    def test_text():
        '''
        Django doesn't validate text field, so it's just smoke test
        '''
        qs = AllFieldsModel.objects.filter(text=BindParam('text')).prepare()
        qs.execute(text='text')

    def test_time(self):
        qs = AllFieldsModel.objects.filter(time=BindParam('time')).prepare()
        qs.execute(time=time())
        qs.execute(time='14:20')
        with self.assertRaises(ValidationError):
            qs.execute(time='not time')

    def test_url(self):
        qs = AllFieldsModel.objects.filter(url=BindParam('url')).prepare()
        qs.execute(url='https://google.com')
        with self.assertRaises(ValidationError):
            qs.execute(url='not url')

    @staticmethod
    def test_uuid():
        '''
        Django doesn't validate uuid field, so it's just smoke test
        '''
        qs = AllFieldsModel.objects.filter(uuid=BindParam('uuid')).prepare()
        qs.execute(uuid=UUID('12345678123456781234567812345678'))

    @staticmethod
    def test_foreign_key():
        '''
        Django doesn't validate foreign key field, so it's just smoke test
        '''
        qs = AllFieldsModel.objects.filter(foreign_key=BindParam('foreign_key')).prepare()
        m = BigAutoModel.objects.create()
        qs.execute(foreign_key=m)
        qs.execute(foreign_key=m.id)
        qs = AllFieldsModel.objects.filter(foreign_key_id=BindParam('foreign_key')).prepare()
        qs.execute(foreign_key=m)
        qs.execute(foreign_key=m.id)
        qs = AllFieldsModel.objects.filter(foreign_key__id=BindParam('foreign_key')).prepare()
        qs.execute(foreign_key=m)
        qs.execute(foreign_key=m.id)

    def test_big_auto(self):
        qs = BigAutoModel.objects.filter(id=BindParam('id')).prepare()
        qs.execute(id=1)
        qs.execute(id='1')
        with self.assertRaises(ValidationError):
            qs.execute(id='text')
