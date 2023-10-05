import csv

from django.core.management import BaseCommand
from django.db.utils import IntegrityError

from recipes.models import Ingredient


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        try:
            with open('data/ingredients.csv', encoding='UTF-8') as file:
                for row in csv.reader(file):
                    name, measurement_unit = row
                    Ingredient.objects.bulk_create(
                        name=name,
                        measurement_unit=measurement_unit
                    )
                print('Импорт данных завершен!')
        except IntegrityError as error:
            raise IntegrityError(self.style.ERROR(f'Ошибка при записи данных csv:{error}'))
        except FileNotFoundError as error:
            raise FileNotFoundError(self.style.ERROR(f'Файл csv не найден по пути : {error}'))
        except UnicodeDecodeError as error:
            raise FileNotFoundError(self.style.ERROR(f'Ошибка при декодировании данных из csv:{error}'))
