SETUP_CODE = '''
def fetch_all(api_fn, page_key="page_index", max_pages=100, **kw):
    """Call a paginated list API repeatedly (page_index 0,1,2,...) until it returns nothing; returns the concatenated list."""
    items = []
    for i in range(max_pages):
        kw[page_key] = i
        r = api_fn(**kw)
        if isinstance(r, dict):
            lst = None
            for v in r.values():
                if isinstance(v, list):
                    lst = v
                    break
            r = lst if lst is not None else []
        if not r:
            break
        items.extend(r)
    return items

def _num(x):
    try: return float(x)
    except Exception: return None

def filter_products(items, max_price=None, min_price=None, min_rating=None, min_reviews=None):
    """Filter product dicts by price / rating / number of reviews (keys are looked up flexibly)."""
    out = []
    for p in items:
        price = _num(p.get("price"))
        rating = _num(p.get("rating") if p.get("rating") is not None else p.get("average_rating"))
        nrev = _num(p.get("review_count") if p.get("review_count") is not None else p.get("num_reviews", p.get("number_of_reviews")))
        if max_price is not None and (price is None or price > max_price): continue
        if min_price is not None and (price is None or price < min_price): continue
        if min_rating is not None and (rating is None or rating < min_rating): continue
        if min_reviews is not None and (nrev is None or nrev < min_reviews): continue
        out.append(p)
    return out
print("helpers ready: fetch_all, filter_products")
'''

def format_prompt(prompt: str, state: dict) -> str:
    state["_n"] = state.get("_n", 0) + 1
    if state["_n"] == 1:
        prompt += ("\n\nHelpers already defined in this session: fetch_all(api_fn, **kwargs) calls a paginated list API for page_index 0,1,2,... until empty and returns ALL items; "
                   "filter_products(items, max_price=, min_price=, min_rating=, min_reviews=) filters product dicts. Whenever the task asks for the best / highest-rated / cheapest / all / N items "
                   "from a list (products, search results, orders, emails), fetch ALL pages with fetch_all before comparing or choosing, then filter by every constraint stated in the task.")
    return prompt
