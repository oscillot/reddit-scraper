class CandidatesList(object):
    """
    A set made up of `class` Download objects with a specific implementation
    of __contains__ to make `keyword` in work properly. Used for set of
    candidates returned from `class` RedditConnect
    """
    def __init__(self, candidates):
        self.candidates = candidates

    def __contains__(self, item):
        for c in self.candidates:
            if item == c.url:
                return item
            elif item == c:
                return item

    def __len__(self):
        return len(self.candidates)

    def __iter__(self):
        for c in self.candidates:
            yield c

    def add(self, item):
        self.candidates.add(item)

    def remove(self, item):
        for c in self.candidates:
            #allows an object to be removed by url reference
            if c.url == item:
                self.candidates.difference({c})
            elif item in self.candidates:
                self.candidates.difference({item})

    def update(self, item):
        self.candidates.update(item)

    def difference(self, item):
        self.candidates.difference(item)

    def union(self, item):
        return self.candidates.union(item)


class DownloadList(object):
    """
    A list made up of `class` Download objects with a specific implementation
    of __contains__ to make `keyword` in work properly. Used for lists of
    already handled posts and already fetched image urls
    """
    def __init__(self, downloads):
        self.downloads = downloads

    def __contains__(self, item):
        for dl in self.downloads:
            if dl.title == item.title and \
                dl.subreddit == item.subreddit and \
                    dl.url == item.url:
                        return dl

    def __len__(self):
        return len(self.downloads)

    def __iter__(self):
        for d in self.downloads:
            yield d

    def add(self, item):
        self.downloads.add(item)

    def update(self, item):
        self.downloads.update(item)

    def difference(self, item):
        self.downloads.difference(item)

    def union(self, item):
        return self.downloads.union(item)


class Download(object):
    """
    A convenience class, the datatype that comprises a `class` DownloadList
    or a `class` CandidatesList
    """
    def __init__(self, title, subreddit, url, nsfw, cookies=None):
        self.title = title
        self.subreddit = subreddit
        self.url = url
        self.nsfw = nsfw
        self.filename = self.name_from_url()
        self.md5 = None
        self.cookies = cookies

    def name_from_url(self):
        return self.url.split('/')[-1].replace(' ', '_')