import sys
import collections

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
    return (elems[0], Column(*elems))

def get_star_projection_type(table_meta, column_dict):
    projection_type_elements = [s.strip() for s in table_meta["*"].split("~")]
    return [column_dict[p].scala_type for p in projection_type_elements]

def create_for_insert(table_meta, column_dict):
    coll = [item for item in column_dict if item != table_meta["primaryKey"]]
    print "\tdef forInsert = %s <> (%sDataForInsert, %sDataForInsert.unapply _)" % (" ~ ".join(coll), table_meta["table"], table_meta["table"])

def generate_parts(table_meta, column_dict):
    partition = 1
    i = 0
    coll = []
    case_classes = []

    for key in column_dict:
        coll.append(key)
        i += 1
        if i >= SCALA_MAX_TUPLE_SIZE:
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
        create_for_insert(table_meta, column_dict)
        case_classes.append(coll)

    _all = ["part%s" % str(c_i + 1) for c_i in range(len(case_classes))]

    if len(column_dict) > SCALA_MAX_TUPLE_SIZE:
        print "\tdef all = (%s)" % ",".join(_all)

    return case_classes

def generate_case_class(case_class_data, column_dict):
    return ", ".join(["%s: %s" % (item, column_dict[item].scala_type) for item in case_class_data])

def generate_insertion_case_class_data(table_meta, case_class, column_dict):
    coll = ["%s: %s" % (item, column_dict[item].scala_type) for item in column_dict if item != table_meta["primaryKey"]]
    return ", ".join(coll)

def generate_insertion_case_class(table_meta, case_class, column_dict):
    print "\ncase class %sDataForInsert(%s)" % (table_meta["table"], generate_insertion_case_class_data(table_meta, case_class, column_dict))

def generate_case_classes(table_meta, case_classes, column_dict):
    bigcase = []
    bigcasetypes = []
    ids = []

    for (class_id, cc) in enumerate(case_classes, start=1):
        print "\ncase class %sData%s(%s)" % (table_meta["table"], class_id, generate_case_class(cc, column_dict))
        bigcase.append("data%s: %sData%s" % (class_id, table_meta["table"], class_id))
        bigcasetypes.append("%sData%s" % (table_meta["table"], class_id))
        ids.append("someValue._%s" % class_id)

    if len(column_dict) < SCALA_MAX_TUPLE_SIZE:
        generate_insertion_case_class(table_meta, case_classes[0], column_dict)
        return

    print "\ncase class %sData(%s) {" % (table_meta["table"], ",".join(bigcase))

    for (cc_id, cc) in enumerate(case_classes, start=1):
        for item in cc:
            print "\tdef %s = data%s.%s" % (item, cc_id, item)

    print "}"
    print "\nobject %sConversions {" % table_meta["table"]
    print "\timplicit def to%sData(someValue: (%s)) = {" % (table_meta["table"], ",".join(bigcasetypes))
    print "\t\t%sData(%s)" % (table_meta["table"], ",".join(ids))
    print "\t}"
    print "}"

def get_from_meta(table_meta, item):
    if table_meta.has_key(item):
        return [x.strip() for x in table_meta[item].split("|")]
    else:
        return []

def generate_options(column, table_meta):
    auto_inc = get_from_meta(table_meta, "autoInc")
    foreign_keys = get_from_meta(table_meta, "foreignKeys")
    items = ['"%s"' % column.database_name]
    if column.scala_name == table_meta["primaryKey"]:
        items.append("O.PrimaryKey")
    if column.scala_name in auto_inc:
        items.append("O.AutoInc")
    return ", ".join(items)


def generate_from_dict(table_meta, column_dict, direct_lines):
    if table_meta["*"] == "all":
        print """object %s extends Table[%sData1]("%s") {""" % (table_meta["table"], table_meta["table"], table_meta["dbname"])        
    else:
        projection_type_list = get_star_projection_type(table_meta, column_dict)
        print """object %s extends Table[(%s)]("%s") {""" % (table_meta["table"], ",".join(projection_type_list), table_meta["dbname"])
    case_classes = generate_parts(table_meta, column_dict)
    print "\tdef * = %s" % table_meta["*"]
    for key, val in column_dict.iteritems():
        print '\tdef %s = column[%s](%s)' % (key, val.scala_type, generate_options(val, table_meta))

    for line in direct_lines:
        print "\t" + line

    print "}"
    generate_case_classes(table_meta, case_classes, column_dict)

def get_table_metadata(line):
    table_meta = {}
    elems = [s.strip() for s in line.split(",")]
    table_meta = dict((k, v) for k, v in (elem.split("=") for elem in elems))
    return table_meta

def generate_slick_file_for(filename):
    f = open(filename)
    column_dict = collections.OrderedDict()
    direct_lines = []
    for line in f.readlines():
        if line.startswith("table"):
            table_meta = get_table_metadata(line)
        else:
            elements = line.split(":")
            if len(elements) == 3:
                (name, column) = get_data_from_line(elements)
                column_dict[name] = column
            elif line.startswith("def"):
                direct_lines.append(line)
            else:
                print line.strip()
    generate_from_dict(table_meta, column_dict, direct_lines)
    
if __name__ == "__main__":
    generate_slick_file_for(sys.argv[1])
