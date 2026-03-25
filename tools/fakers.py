from faker import Faker


class Fake:
    """Класс для генерации случайных тестовых данных."""

    def __init__(self, faker: Faker) -> None:
        self.faker = faker

    def seller_id(self) -> int:
        """Генерирует случайный sellerID в диапазоне 111111-999999."""
        return self.faker.random_int(111111, 999999)

    def item_name(self) -> str:
        """Генерирует случайное название объявления."""
        return self.faker.sentence(nb_words=3)

    def price(self) -> int:
        """Генерирует случайную цену."""
        return self.faker.random_int(1, 1_000_000)

    def likes(self) -> int:
        """Генерирует случайное количество лайков."""
        return self.faker.random_int(0, 10_000)

    def view_count(self) -> int:
        """Генерирует случайное количество просмотров."""
        return self.faker.random_int(0, 100_000)

    def contacts(self) -> int:
        """Генерирует случайное количество контактов."""
        return self.faker.random_int(0, 5_000)

    def uuid4(self) -> str:
        """Генерирует случайный UUID4."""
        return self.faker.uuid4()


fake = Fake(faker=Faker())
