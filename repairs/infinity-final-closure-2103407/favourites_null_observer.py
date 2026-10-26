"""Interpret Kodi's actual nullable Favorites array; no assertion or API waiver."""
ANCHOR="    path=Path(root);output=path/('navigation-ready-'+cycle+'.json')"
BLOCK='''    if mode=='final-actions':
        class NativeFavouritesObservation:
            def __init__(self,actual):
                self.actual=actual
            def __getattr__(self,name):
                return getattr(self.actual,name)
            def rpc(self,method,params=None):
                value=self.actual.rpc(method,params)
                if method!='Favourites.GetFavourites':
                    return value
                result.setdefault('raw_native_favourites',[]).append(value)
                if not isinstance(value,dict) or 'favourites' not in value:
                    raise RuntimeError('Malformed native Favorites response')
                rows=value['favourites']
                if rows is None:
                    limits=value.get('limits')
                    if not isinstance(limits,dict) or any(
                            type(limits.get(key)) is not int or limits[key]!=0
                            for key in ('start','end','total')):
                        raise RuntimeError('Null native Favorites without exact empty limits')
                    return dict(value,favourites=[])
                if not isinstance(rows,list) or any(not isinstance(row,dict) for row in rows):
                    raise RuntimeError('Malformed native Favorites rows')
                return value
        ui=NativeFavouritesObservation(ui)
'''


def instrument(text):
    if text.count(ANCHOR)!=1 or BLOCK in text:raise ValueError('Original fixture output anchor differs')
    result=text.replace(ANCHOR,BLOCK+ANCHOR,1)
    if restore(result)!=text:raise ValueError('Original Favorites assertions changed')
    return result


def restore(text):
    return text.replace(BLOCK,'',1)
