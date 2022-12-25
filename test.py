# import asyncio
# from cron.cron_job import fetch_tweet_mentions

# asyncio.run(fetch_tweet_mentions())

from app.deta_tweet import add_messi_nft

messi_nft_ipfs_hash = [
    "bafkreic7evydbmqihn26conqhui433frpu6cl4qryxw3cravr2j6uuiplq",
    "bafkreif5is234mm62dwrl5n2gmgfucexmocndtliliyc7faii3bjnghwra",
    "bafkreihz77xf6cxjyt5wz34sdbz7pz4j5m4yy6tepmh2ixa5fi7ixc7oq4",
    "bafkreihkz7lacgdjy5rkic53gmmwupxl4uo2iypsx7y62ifnbdjxg2uoay",
    "bafkreickoabmeerua67hdrttohxy76bke2dkdd2rvrxivqyxcfy6go7tye",
    "bafkreic245wdrl7fu5mci5oaoog64inikrudfh3stiwonqqdpfh772wfoy",
    "bafkreia35jevoi6ziwyqrt3ftridnccahoiln23zy26oqppvuyk7ifzdoy",
    "bafkreiebod22at7lykactzmku35fho3b4oy7yhqfbq3xqv326e3s25q35u",
    "bafkreibwmjjw5x5zohe2o4gxstyunkcv7cgv3jh63sxwjesvio7f6he2pm",
    "bafkreidzldnxtiprdnzr6zwfpchadoupnovkgms5fhfk5jajyyqgxygnxu",
    "bafkreif4ppzyw7uupwwquezbqg6it56nhhhjjqjnm7i6efqedsrv2by5cu",
    "bafkreibabtdhfuozmoh6fdzzyl7rbsoqtrdlbtbcjfmj2f2tylzveethda",
    "bafkreidsffxtvk7z4psiwjhier63aiyo5m3uxrxihhvh4dfxxmir6ajapm",
    "bafkreifs4ec5mekoldg3n3khj5yhjp66fxtmrd5euy2akvlzxj2dhdjzwq",
    "bafkreienonwdyala7x62um46xaz4xxsvuqjgbwy5zkaxc36makeeq6sgfq",
]

for nft in messi_nft_ipfs_hash:
    nft_url = f"https://{nft}.ipfs.nftstorage.link/"
    add_messi_nft(nft, nft_url)
    print("done")
