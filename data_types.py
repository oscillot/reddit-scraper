class CandidatesList(object):
    """
    A list made up of `class` Download objects with a specific implementation
    of __contains__ to make `keyword` in work properly. Used for list of
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

    def remove(self, item):
        for c in self.candidates:
            if c.url == item:
                self.candidates.remove(c)
            elif item in self.candidates:
                self.candidates.remove(item)

    def update(self, update_object):
        self.candidates.update(update_object)

    def __len__(self):
        return len(self.candidates)

    def __iter__(self):
        for c in self.candidates:
            yield c


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

    def append(self, item):
        self.downloads.append(item)


class Download(object):
    """
    A convenience class, the datatype that comprises a `class` DownloadList
    or a `class` CandidatesList
    """
    def __init__(self, title, subreddit, url, cookies=None):
        self.title = title
        self.subreddit = subreddit
        self.url = url
        self.filename = self.name_from_url()
        self.md5 = None
        self.cookies = cookies

    def name_from_url(self):
        return self.url.split('/')[-1].replace(' ', '_')