ref_new = "/data/home/jdang/SIPO_PDF_B/ocr_results/refs/refs_new.txt"
ref_old = "/data/home/jdang/SIPO_PDF_B/ocr_results/refs/refs.txt"
ref_comb = "/data/home/jdang/SIPO_PDF_B/ocr_results/refs/refs_comb.txt"
pnr_set = set()

with open(ref_new, "r") as f:
    for line in f.readlines():
        pnr_set.add(line.split("|")[0])

with open(ref_old,"r") as g:
    for line in g.readlines():
        pnr = line.split("|")[0]
        ref = line.split("|")[1].replace("\n","")
        if pnr not in pnr_set:
            with open(ref_comb,"a") as h:
                h.write(pnr + "|" + ref + "\n")