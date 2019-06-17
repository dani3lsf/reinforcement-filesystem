import json
import argparse


THRESHOLD = 3

def most_accessed_files(files_data):
    hits = [(file, files_data['hits'][file]) for file in files_data['hits']]
    hits = sorted(hits, key=lambda x: x[1], reverse=True)
    top_hits = [(hit[0],hit[1],files_data["files_cloud"][hit[0]]) for hit in hits if hit[1] > THRESHOLD]
    return top_hits
    

def process_file(file_name1, file_name2):
    res = {'file1': {}, 'file2': {}}

    it_counter = 0

    with open(file_name1) as json_file1:  
        its_file1 = json.load(json_file1)
        for it in its_file1:
            it_counter += 1
            files_accessed_file1 = most_accessed_files(its_file1.get(it))
            res['file1'][it] = files_accessed_file1
    
    with open(file_name2) as json_file2:  
        its_file2 = json.load(json_file2)
        for it in its_file2:
            files_accessed_file2 = most_accessed_files(its_file2.get(it))
            res['file2'][it] = files_accessed_file2

    for it in range(0, it_counter):
        print('Iteration ' + str(it) + ':')
        position_pointer = 0
        while(len(res['file1'][str(it)]) > position_pointer and len(res['file2'][str(it)]) > position_pointer):
            (file_name1, file_hit1, file_cloud1) =  res['file1'][str(it)][position_pointer]
            (file_name2, file_hit2, file_cloud2) =  res['file2'][str(it)][position_pointer]
            print(str(file_name1) + "\t" + str(file_hit1) + "\t" + str(file_cloud1) + '\t\t'+ str(file_name2) + "\t" + str(file_hit2) + "\t" + str(file_cloud2))
            position_pointer += 1

        while(len(res['file1'][str(it)]) > position_pointer):
            (file_name1, file_hit1, file_cloud1) =  res['file1'][str(it)][position_pointer]
            print(str(file_name1) + "\t" + str(file_hit1) + "\t" + str(file_cloud1) + '\t\t'+ str(file_name2) + "\t" + str(file_hit2) + "\t" + str(file_cloud2))
            position_pointer += 1


        while(len(res['file2'][str(it)]) > position_pointer):
            (file_name2, file_hit2, file_cloud2) =  res['file2'][str(it)][position_pointer]
            print('-------' + "\t" + '--' + "\t" + '-' + '\t\t'+ str(file_name2) + "\t" + str(file_hit2) + "\t" + str(file_cloud2))
            position_pointer += 1

def main(files):

    files_data = {}
    process_file(files[0].name, files[1].name)
    # print(files)
    # for f in files:
    #     file_name = f.name
    #     process_file(file_name)
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('files', type=argparse.FileType('r'), nargs='+', help="json_files")
    args = parser.parse_args()
    main(args.files)