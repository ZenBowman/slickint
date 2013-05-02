import sys

SCALA_MAX_TUPLE_SIZE = 20

class Column:
    def __init__ (self, scala_name, scala_type, database_name):
        self.scala_name = scala_name
        self.scala_type = de_optionize(scala_type)
        self.database_name = database_name

def de_optionize(some_string):
    if some_string.endswith("?"):
        return "Option[%s]" % some_string[:-1]
    else:
        return some_string

def get_data_from_line(elems):
    elems = [s.strip() for s in elems]
    return (elems[0], Column(elems[0], elems[1], elems[2]))

def get_star_projection_type(table_meta, column_dict):
    projection_type_list = []
    projection_type_elements = [s.strip() for s in table_meta["*"].split("~")]
    for p in projection_type_elements:
        projection_type_list.append(column_dict[p].scala_type)
    return projection_type_list

def generate_parts(table_meta, column_dict):
    partition = 1
    i = 0
    coll = []
    case_classes = []

    for key in column_dict:
        coll.append(key)
        i += 1
        if i >= 20:
            print "\tdef part%s = %s <> (%sData%s, %sData%s.unapply _)" % (partition, " ~ ".join(coll), table_meta["table"], partition, table_meta["table"], partition)
            case_classes.append(coll)
            coll = []
            partition += 1
            i = 0

    if (i > 0) and (len(column_dict) > SCALA_MAX_TUPLE_SIZE):
        print "\tdef part%s = %s <> (%sData%s, %sData%s.unapply _)" % (partition, " ~ ".join(coll), table_meta["table"], partition, table_meta["table"], partition)
        case_classes.append(coll)
    else:
        print "\tdef all = %s <> (%sData%s, %sData%s.unapply _)" % (" ~ ".join(coll), table_meta["table"], partition, table_meta["table"], partition)
        case_classes.append(coll)

    _all = []
    for c_i in range(len(case_classes)):
        _all.append("part%s" % str(c_i + 1))

    if len(column_dict) > SCALA_MAX_TUPLE_SIZE:
        print "\tdef all = (%s)" % ",".join(_all)

    return case_classes

def generate_case_class(case_class_data, column_dict):
    vals = []
    for item in case_class_data:
        vals.append("%s: %s" % (item, column_dict[item].scala_type))
    return ",".join(vals)

def generate_case_classes(table_meta, case_classes, column_dict):
    bigcase = []
    bigcasetypes = []
    ids = []
    class_id = 1
    for cc in case_classes:
        print "\ncase class %sData%s(%s)" % (table_meta["table"], class_id, generate_case_class(cc, column_dict))
        bigcase.append("data%s: %sData%s" % (class_id, table_meta["table"], class_id))
        bigcasetypes.append("%sData%s" % (table_meta["table"], class_id))
        ids.append("someValue._%s" % class_id)
        class_id += 1

    if len(column_dict) < SCALA_MAX_TUPLE_SIZE:
        return

    print "\ncase class %sData(%s) {" % (table_meta["table"], ",".join(bigcase))
    cc_id = 1
    for cc in case_classes:
        for item in cc:
            print "\tdef %s = data%s.%s" % (item, cc_id, item)
        cc_id += 1
    print "}"
    print "\nobject %sConversions {" % table_meta["table"]
    print "\timplicit def to%sData(someValue: (%s)) = {" % (table_meta["table"], ",".join(bigcasetypes))
    print "\t\t%sData(%s)" % (table_meta["table"], ",".join(ids))
    print "\t}"
    print "}"

def generate_from_dict(table_meta, column_dict):
    projection_type_list = get_star_projection_type(table_meta, column_dict)
    print """object %s extends Table[(%s)]("%s") {""" % (table_meta["table"], ",".join(projection_type_list), table_meta["dbname"])
    case_classes = generate_parts(table_meta, column_dict)
    print "\tdef * = %s" % table_meta["*"]    
    for key in column_dict:
        val = column_dict[key]
        print '\tdef %s = column[%s]("%s")' % (key, val.scala_type, val.database_name)
    print "}"
    generate_case_classes(table_meta, case_classes, column_dict)

def get_table_metadata(line):
    table_meta = {}
    elems = [s.strip() for s in line.split(",")]
    for elem in elems:
        (e1, e2) = elem.split("=")
        table_meta[e1] = e2
    return table_meta

def generate_slick_file_for(filename):
    f = open(filename)
    column_dict = {}
    for line in f.readlines():
        if line.startswith("table"):
            table_meta = get_table_metadata(line)
        else:
            elements = line.split(":")
            if len(elements) == 3:
                (name, column) = get_data_from_line(elements)
                column_dict[name] = column
            else:
                print line.strip()
    generate_from_dict(table_meta, column_dict)
    
if __name__ == "__main__":
    generate_slick_file_for(sys.argv[1])
