from django.core.validators import RegexValidator

alphabet_validator = RegexValidator(r'^[a-zA-Zа-яА-я]*$',
                                    'Only alphanumeric characters are allowed.'
                                    )
