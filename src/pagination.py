import math


class Page(object):
    def __init__(self, paginator, objects_list, number):
        self.number = number
        self.paginator = paginator
        self.objects_list = objects_list

    def has_next(self):
        offset = self.number * self.paginator.per_page
        return offset < self.paginator.count()

    def next_page_number(self):
        if not self.has_next():
            return None
        return self.number + 1

    def has_previous(self):
        return self.number > 1

    def previous_page_number(self):
        if self.number == 1:
            return None
        return self.number - 1


class Paginator(object):
    page_cls = Page

    def __init__(self, objects_list, per_page):
        self.objects_list = objects_list
        self.per_page = per_page

    def count(self):
        if not hasattr(self, '_cached_count'):
            try:
                self._cached_count = self.objects_list.count()
            except AttributeError:
                self._cached_count = len(self.objects_list)
        return self._cached_count

    def page_count(self):
        return int(math.ceil(float(self.count()) / self.per_page))

    def __len__(self):
        return self.count()

    def page(self, number):
        objects = self.objects_list.paginate(number, self.per_page)
        return self.page_cls(self, tuple(objects), number)
