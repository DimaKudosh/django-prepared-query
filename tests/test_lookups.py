from datetime import datetime, date, time
from django.test import TestCase
from django.core.exceptions import ValidationError
from test_app.models import Author
from django_prepared_query import BindParam, BindArray, NotSupportedLookup, PreparedStatementException


class PreparedStatementsTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        created_date = datetime(year=2015, month=5, day=5, hour=5, minute=5, second=5)
        Author.objects.create(name='Kazuo Ishiguro', age=50, gender='m')
        Author.objects.create(name='Bob Dylan', age=51, gender='m')
        Author.objects.create(name='Svetlana Alexievich', age=52, gender='f', created_at=created_date)
        Author.objects.create(name='Patrick Modiano', age=53, gender='m')

    @classmethod
    def tearDownClass(cls):
        Author.objects.delete()

    def test_exact_lookup(self):
        name = 'Svetlana Alexievich'
        qs = Author.objects.filter(name__exact=BindParam('name')).prepare()
        result = list(Author.objects.filter(name__exact=name))
        self.assertListEqual(qs.execute(name=name), result)

    def test_iexact_lookup(self):
        name = 'Svetlana Alexievich'
        qs = Author.objects.filter(name__iexact=BindParam('name')).prepare()
        result = list(Author.objects.filter(name__iexact=name))
        self.assertListEqual(qs.execute(name=name), result)

    def test_contains_lookup(self):
        name_part = 'tlana'
        qs = Author.objects.filter(name__contains=BindParam('name')).prepare()
        result = list(Author.objects.filter(name__contains=name_part))
        self.assertListEqual(qs.execute(name=name_part), result)

    def test_icontains_lookup(self):
        name_part = 'Tlana'
        qs = Author.objects.filter(name__icontains=BindParam('name')).prepare()
        result = list(Author.objects.filter(name__icontains=name_part))
        self.assertListEqual(qs.execute(name=name_part), result)

    def test_startswith_lookup(self):
        name = 'Svetlana'
        qs = Author.objects.filter(name__startswith=BindParam('name')).prepare()
        result = list(Author.objects.filter(name__startswith=name))
        self.assertListEqual(qs.execute(name=name), result)

    def test_istartswith_lookup(self):
        name = 'svetlana'
        qs = Author.objects.filter(name__istartswith=BindParam('name')).prepare()
        result = list(Author.objects.filter(name__istartswith=name))
        self.assertListEqual(qs.execute(name=name), result)

    def test_endswith_lookup(self):
        name = 'vich'
        qs = Author.objects.filter(name__endswith=BindParam('name')).prepare()
        result = list(Author.objects.filter(name__endswith=name))
        self.assertListEqual(qs.execute(name=name), result)

    def test_iendswith_lookup(self):
        name = 'Vich'
        qs = Author.objects.filter(name__iendswith=BindParam('name')).prepare()
        result = list(Author.objects.filter(name__iendswith=name))
        self.assertListEqual(qs.execute(name=name), result)

    def test_range_lookup(self):
        start = 52
        end = 53
        qs = Author.objects.filter(age__range=(BindParam('start'), BindParam('end'))).prepare()
        result = list(Author.objects.filter(age__range=(start, end)))
        self.assertListEqual(qs.execute(start=start, end=end), result)

    def test_gt_lookup(self):
        qs = Author.objects.filter(age__gt=BindParam('age')).prepare()
        result = list(Author.objects.filter(age__gt=52))
        self.assertListEqual(qs.execute(age=52), result)

    def test_gte_lookup(self):
        qs = Author.objects.filter(age__gte=BindParam('age')).prepare()
        result = list(Author.objects.filter(age__gte=52))
        self.assertListEqual(qs.execute(age=52), result)

    def test_lt_lookup(self):
        qs = Author.objects.filter(age__lt=BindParam('age')).prepare()
        result = list(Author.objects.filter(age__lt=52))
        self.assertListEqual(qs.execute(age=52), result)

    def test_lte_lookup(self):
        qs = Author.objects.filter(age__lte=BindParam('age')).prepare()
        result = list(Author.objects.filter(age__lte=52))
        self.assertListEqual(qs.execute(age=52), result)

    def test_date_lookup(self):
        d = date(year=2015, month=5, day=5)
        qs = Author.objects.filter(created_at__date=BindParam('date')).prepare()
        result = list(Author.objects.filter(created_at__date=d))
        self.assertListEqual(qs.execute(date=d), result)

    def test_year_lookup(self):
        year = 2015
        qs = Author.objects.filter(created_at__year=BindParam('year')).prepare()
        result = list(Author.objects.filter(created_at__year=year))
        self.assertListEqual(qs.execute(year=year), result)

    def test_month_lookup(self):
        month = 5
        qs = Author.objects.filter(created_at__month=BindParam('month')).prepare()
        result = list(Author.objects.filter(created_at__month=month))
        self.assertListEqual(qs.execute(month=month), result)

    def test_day_lookup(self):
        day = 5
        qs = Author.objects.filter(created_at__day=BindParam('day')).prepare()
        result = list(Author.objects.filter(created_at__day=day))
        self.assertListEqual(qs.execute(day=day), result)

    def test_week_lookup(self):
        week = 1
        qs = Author.objects.filter(created_at__week=BindParam('week')).prepare()
        result = list(Author.objects.filter(created_at__week=week))
        self.assertListEqual(qs.execute(week=week), result)

    def test_week_day_lookup(self):
        week_day = 1
        qs = Author.objects.filter(created_at__week_day=BindParam('week_day')).prepare()
        result = list(Author.objects.filter(created_at__week_day=week_day))
        self.assertListEqual(qs.execute(week_day=week_day), result)

    def test_time_lookup(self):
        t = time(5, 5)
        qs = Author.objects.filter(created_at__time=BindParam('time')).prepare()
        result = list(Author.objects.filter(created_at__time=t))
        self.assertListEqual(qs.execute(time=t), result)

    def test_hour_lookup(self):
        hour = 5
        qs = Author.objects.filter(created_at__hour=BindParam('hour')).prepare()
        result = list(Author.objects.filter(created_at__hour=hour))
        self.assertListEqual(qs.execute(hour=hour), result)

    def test_minute_lookup(self):
        minute = 5
        qs = Author.objects.filter(created_at__minute=BindParam('minute')).prepare()
        result = list(Author.objects.filter(created_at__minute=minute))
        self.assertListEqual(qs.execute(minute=minute), result)

    def test_second_lookup(self):
        second = 5
        qs = Author.objects.filter(created_at__second=BindParam('second')).prepare()
        result = list(Author.objects.filter(created_at__second=second))
        self.assertListEqual(qs.execute(second=second), result)

    def test_regex_lookup(self):
        regex = r'^Svet.+Alex.+'
        qs = Author.objects.filter(name__regex=BindParam('regex')).prepare()
        result = list(Author.objects.filter(name__regex=regex))
        self.assertListEqual(qs.execute(regex=regex), result)

    def test_iregex_lookup(self):
        regex = r'^Svet.+Alex.+'
        qs = Author.objects.filter(name__iregex=BindParam('regex')).prepare()
        result = list(Author.objects.filter(name__iregex=regex))
        self.assertListEqual(qs.execute(regex=regex), result)

    def test_in_lookup(self):
        ids = [1, 3]
        with self.assertRaises(PreparedStatementException):
            qs = Author.objects.filter(id__in=BindParam('ids')).prepare()
        qs = Author.objects.filter(id__in=BindArray('ids', len(ids))).prepare()
        self.assertEqual(qs.execute(ids=[]), [])
        self.assertEqual(qs.execute(ids=ids[:1]), list(Author.objects.filter(id__in=ids[:1])))
        self.assertEqual(qs.execute(ids=ids), list(Author.objects.filter(id__in=ids)))
        with self.assertRaises(ValidationError):
            ids.append(5)
            qs.execute(ids=ids)

    def test_isnull_lookup(self):
        with self.assertRaises(NotSupportedLookup):
            Author.objects.filter(id__isnull=BindParam('null')).prepare()
