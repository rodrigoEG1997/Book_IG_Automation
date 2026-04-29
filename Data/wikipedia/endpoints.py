def imge_bio_link(name):
    name = name.replace(" ", "_")
    return {
        "endpoint": f"page/summary/{name}",
        "params": {}
    }

