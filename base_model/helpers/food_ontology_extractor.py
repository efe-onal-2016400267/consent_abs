from ontolearner.ontology import BBCFood

ontology = BBCFood()

ontology.load("/Users/efeonal/Documents/UU_Courses/Thesis/bbc_food_ontology/food.ttl")

# Extract datasets
data = ontology.extract()

# Access specific relations
term_types = data.term_typings
taxonomic_relations = data.type_taxonomies
non_taxonomic_relations = data.type_non_taxonomic_relations

print(data)

# Get all classes
print("=== Classes ===")
classes = list(data.term_typings.keys())
for cls in classes:
    print(cls)

# Get all individuals (instances)
print("\n=== Individuals ===")
individuals = list(data.type_non_taxonomic_relations.keys())
for ind in individuals:
    print(ind)


print("efe")