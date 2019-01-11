def json_to_attrs(obj, json_res, types=(str, int, type(None), )):
	for key, val in json_res.items():
		if type(val) in types:
			setattr(obj, key, val if type(val) is not str else val.strip())