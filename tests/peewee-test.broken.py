import unittest
from datetime import date, datetime, timezone
from uuid import uuid4

from peewee import (
    Model, CharField, DateField, DateTimeField, IntegerField, BooleanField,
    ForeignKeyField, SqliteDatabase, UUIDField, fn, JOIN, IntegrityError,
    Check
)

# ---------------------------------------------------------------------------
# Shared in-memory DB (fast, isolated per process)
# ---------------------------------------------------------------------------
db = SqliteDatabase(
    ':memory:',
    pragmas={
        'journal_mode': 'wal',
        'cache_size': -1024 * 64,
        'foreign_keys': 1,   # ensure FK actions enforced on SQLite
        'synchronous': 0,
    },
)

# ---------------------------------------------------------------------------
# Original quickstart coverage (Person / Pet)
# ---------------------------------------------------------------------------
class Person(Model):
    name = CharField()
    birthday = DateField()
    class Meta:
        database = db

class Pet(Model):
    owner = ForeignKeyField(Person, backref='pets')
    name = CharField()
    animal_type = CharField()
    class Meta:
        database = db


class PeeweeQuickstartTests(unittest.TestCase):
    def setUp(self):
        db.connect(reuse_if_open=True)
        db.create_tables([Person, Pet])
        self.seed_data()

    def tearDown(self):
        db.drop_tables([Pet, Person])
        db.close()

    # --- Helpers -------------------------------------------------------------
    def seed_data(self):
        # People
        self.uncle_bob = Person.create(name='Bob', birthday=date(1960, 1, 15))
        self.grandma = Person.create(name='Grandma', birthday=date(1935, 3, 1))
        self.herb = Person.create(name='Herb', birthday=date(1950, 5, 5))

        # Update Grandma's name (save should return rows updated == 1)
        self.grandma.name = 'Grandma L.'
        rows = self.grandma.save()
        assert rows == 1

        # Pets
        self.bob_kitty = Pet.create(owner=self.uncle_bob, name='Kitty', animal_type='cat')
        self.herb_fido = Pet.create(owner=self.herb, name='Fido', animal_type='dog')
        self.herb_mittens = Pet.create(owner=self.herb, name='Mittens', animal_type='cat')
        self.herb_mittens_jr = Pet.create(owner=self.herb, name='Mittens Jr', animal_type='cat')

        # Remove Mittens (delete_instance returns rows deleted == 1)
        del_rows = self.herb_mittens.delete_instance()
        assert del_rows == 1

        # Reassign Fido from Herb to Bob
        self.herb_fido.owner = self.uncle_bob
        self.herb_fido.save()

    # --- Tests: Model & Basics ----------------------------------------------
    def test_model_definition_and_table_creation(self):
        # Basic smoke checks: counts and schema assumptions.
        self.assertEqual(Person.select().count(), 3)
        self.assertEqual(Pet.select().count(), 3)  # Kitty, Fido, Mittens Jr

        # Grandma was renamed and persisted.
        grandma = Person.get(Person.name == 'Grandma L.')
        self.assertEqual(grandma.birthday, date(1935, 3, 1))

    def test_save_returns_rowcount_on_update(self):
        bob = Person.get(Person.name == 'Bob')
        bob.name = 'Uncle Bob'
        rows = bob.save()
        self.assertEqual(rows, 1)
        self.assertTrue(Person.select().where(Person.name == 'Uncle Bob').exists())

    def test_delete_instance_returns_rowcount(self):
        count_before = Pet.select().count()
        rows = self.herb_mittens_jr.delete_instance()
        self.assertEqual(rows, 1)
        self.assertEqual(Pet.select().count(), count_before - 1)

    # --- Tests: Retrieving singles & lists ----------------------------------
    def test_get_single_record(self):
        grandma = Person.get(Person.name == 'Grandma L.')
        self.assertEqual(grandma.birthday, date(1935, 3, 1))

        # Equivalent via select().where(...).get()
        grandma2 = Person.select().where(Person.name == 'Grandma L.').get()
        self.assertEqual(grandma2.id, grandma.id)

    def test_list_all_people(self):
        names = [p.name for p in Person.select().order_by(Person.name)]
        self.assertEqual(names, ['Bob', 'Grandma L.', 'Herb'])

    # --- Tests: Joins & filtering -------------------------------------------
    def test_list_all_cats_with_owner_names_joined(self):
        q = (Pet
             .select(Pet, Person)
             .join(Person)
             .where(Pet.animal_type == 'cat')
             .order_by(Pet.name))
        results = [(p.name, p.owner.name) for p in list(q)]
        self.assertEqual(results, [('Kitty', 'Bob'), ('Mittens Jr', 'Herb')])

    def test_get_bobs_pets_via_join_on_person_name(self):
        names = [p.name for p in Pet.select().join(Person).where(Person.name == 'Bob').order_by(Pet.name)]
        self.assertEqual(names, ['Fido', 'Kitty'])

    def test_get_bobs_pets_via_owner_instance(self):
        uncle_bob = Person.get(Person.name == 'Bob')
        names = [p.name for p in Pet.select().where(Pet.owner == uncle_bob).order_by(Pet.name)]
        self.assertEqual(names, ['Fido', 'Kitty'])

    def test_ordering(self):
        uncle_bob = Person.get(Person.name == 'Bob')
        ordered = [p.name for p in Pet.select().where(Pet.owner == uncle_bob).order_by(Pet.name)]
        self.assertEqual(ordered, ['Fido', 'Kitty'])

        youngest_to_oldest = [(p.name, p.birthday) for p in Person.select().order_by(Person.birthday.desc())]
        self.assertEqual(youngest_to_oldest, [
            ('Bob', date(1960, 1, 15)),
            ('Herb', date(1950, 5, 5)),
            ('Grandma L.', date(1935, 3, 1)),
        ])

    def test_combining_filters(self):
        d1940 = date(1940, 1, 1)
        d1960 = date(1960, 1, 1)
        # People before 1940 OR after 1959
        q1 = (Person
              .select()
              .where((Person.birthday < d1940) | (Person.birthday > d1960)))
        res1 = [(p.name, p.birthday) for p in q1.order_by(Person.birthday)]
        self.assertEqual(res1, [
            ('Grandma L.', date(1935, 3, 1)),
            ('Bob', date(1960, 1, 15)),
        ])

        # People between 1940 and 1960 (inclusive)
        q2 = (Person
              .select()
              .where(Person.birthday.between(d1940, d1960)))
        res2 = [(p.name, p.birthday) for p in q2]
        self.assertEqual(res2, [('Herb', date(1950, 5, 5))])

    # --- Tests: Aggregates & LEFT OUTER join --------------------------------
    def test_aggregate_counts_per_person(self):
        q = (Person
             .select(Person, fn.COUNT(Pet.id).alias('pet_count'))
             .join(Pet, JOIN.LEFT_OUTER)
             .group_by(Person)
             .order_by(Person.name))
        counts = {p.name: p.pet_count for p in list(q)}
        # Bob has Fido + Kitty = 2, Grandma L. has 0, Herb has Mittens Jr = 1
        self.assertEqual(counts, {'Bob': 2, 'Grandma L.': 0, 'Herb': 1})

    # --- Tests: Prefetch (avoid duplicate parent rows) ----------------------
    def test_prefetch_people_and_pets(self):
        # Order people for deterministic iteration; prefetch turns backrefs into lists.
        q = Person.select().order_by(Person.name).prefetch(Pet)
        collected = {}
        for person in list(q):
            pet_names = sorted([pet.name for pet in person.pets])  # backref is a list after prefetch
            collected[person.name] = pet_names
        self.assertEqual(collected, {
            'Bob': ['Fido', 'Kitty'],
            'Grandma L.': [],
            'Herb': ['Mittens Jr'],
        })

    # --- Tests: SQL functions (Lower + Substr) ------------------------------
    def test_sql_functions_lower_and_substr(self):
        expr = fn.Lower(fn.Substr(Person.name, 1, 1)) == 'g'
        g_people = [p.name for p in Person.select().where(expr)]
        self.assertEqual(g_people, ['Grandma L.'])

    # --- Tests: Connection management sanity --------------------------------
    def test_connection_open_and_close(self):
        # setUp has opened the connection.
        self.assertFalse(db.is_closed())
        db.close()
        self.assertTrue(db.is_closed())
        # Re-open so tearDown can drop tables cleanly.
        db.connect(reuse_if_open=True)


# ---------------------------------------------------------------------------
# Extra coverage: Schema & Model options (no extra deps)
# ---------------------------------------------------------------------------
class CustomBase(Model):
    class Meta:
        database = db

class CustomNamed(CustomBase):
    # Custom table name test
    name = CharField()
    class Meta:
        table_name = 'custom_named'
        database = db

class WithDefaults(CustomBase):
    title = CharField(default='untitled')
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    active = BooleanField(default=True)

class UniqueThing(CustomBase):
    slug = CharField(unique=True)

class WithChecks(CustomBase):
    balance = IntegerField(constraints=[Check('balance >= 0')])


class SchemaAndModelTests(unittest.TestCase):
    def setUp(self):
        db.connect(reuse_if_open=True)
        db.create_tables([CustomNamed, WithDefaults, UniqueThing, WithChecks])

    def tearDown(self):
        db.drop_tables([WithChecks, UniqueThing, WithDefaults, CustomNamed])
        db.close()

    def test_custom_table_name_exists_and_writes(self):
        obj = CustomNamed.create(name='alpha')
        self.assertEqual(CustomNamed.get(CustomNamed.name == 'alpha').id, obj.id)

        # Introspect columns minimally
        cols = [c.name for c in db.get_columns('custom_named')]
        self.assertIn('name', cols)

    def test_defaults_and_callables(self):
        w = WithDefaults.create()
        self.assertEqual(w.title, 'untitled')
        self.assertTrue(isinstance(w.created_at, datetime))
        self.assertTrue(w.active)

    def test_unique_constraint_raises(self):
        UniqueThing.create(slug='x')
        with self.assertRaises(IntegrityError):
            UniqueThing.create(slug='x')

    def test_check_constraint_non_negative(self):
        WithChecks.create(balance=0)
        with self.assertRaises(IntegrityError):
            WithChecks.create(balance=-10)


# ---------------------------------------------------------------------------
# Extra coverage: CRUD, bulk ops, lookups, shapes
# ---------------------------------------------------------------------------
class BulkBase(Model):
    class Meta:
        database = db

class Item(BulkBase):
    name = CharField(index=True)
    qty = IntegerField(default=0)

class Tag(BulkBase):
    name = CharField(unique=True)

class ItemTag(BulkBase):
    item = ForeignKeyField(Item, backref='item_tags', on_delete='CASCADE')
    tag = ForeignKeyField(Tag, backref='tagged_items', on_delete='CASCADE')

class CrudAndBulkTests(unittest.TestCase):
    def setUp(self):
        db.connect(reuse_if_open=True)
        db.create_tables([Item, Tag, ItemTag])

    def tearDown(self):
        db.drop_tables([ItemTag, Tag, Item])
        db.close()

    def test_get_or_create_and_get_or_none(self):
        obj, created = Item.get_or_create(name='widget', defaults={'qty': 5})
        self.assertTrue(created)
        again = Item.get_or_none(Item.name == 'widget')
        self.assertIsNotNone(again)
        self.assertEqual(again.qty, 5)

        obj2, created2 = Item.get_or_create(name='widget', defaults={'qty': 99})
        self.assertFalse(created2)
        self.assertEqual(obj2.id, obj.id)

    def test_insert_many_and_bulk_update(self):
        data = [{'name': f'i{i}', 'qty': i} for i in range(5)]
        Item.insert_many(data).execute()
        self.assertEqual(Item.select().count(), 5)

        # bulk_update: increase qty for even items
        items = list(Item.select().order_by(Item.name))
        for it in items:
            if it.qty % 2 == 0:
                it.qty += 10
        Item.bulk_update([it for it in items if it.qty >= 10], fields=[Item.qty])

        got = {it.name: it.qty for it in Item.select()}
        # Even i (0,2,4) increased by +10:
        self.assertEqual(got['i0'], 10)
        self.assertEqual(got['i1'], 1)
        self.assertEqual(got['i2'], 12)
        self.assertEqual(got['i3'], 3)
        self.assertEqual(got['i4'], 14)

    def test_save_only_fields(self):
        it = Item.create(name='solo', qty=1)
        it.name = 'changed'
        it.qty = 99
        # Save only 'qty'; name should remain unchanged in DB
        it.save(only=[Item.qty])
        refetched = Item.get_by_id(it.id)
        self.assertEqual(refetched.qty, 99)
        self.assertEqual(refetched.name, 'solo')

    def test_exists_and_scalar_shapes(self):
        Item.create(name='a', qty=1)
        Item.create(name='b', qty=2)

        self.assertTrue(Item.select().where(Item.name == 'a').exists())
        total_qty = Item.select(fn.SUM(Item.qty)).scalar()
        self.assertEqual(total_qty, 3)

        # dicts / tuples / namedtuples
        rows_dicts = list(Item.select().order_by(Item.name).dicts())
        self.assertEqual(rows_dicts[0]['name'], 'a')

        rows_tuples = list(Item.select(Item.name, Item.qty).order_by(Item.name).tuples())
        self.assertEqual(rows_tuples[1], ('b', 2))

        rows_nt = list(Item.select(Item.name, Item.qty).order_by(Item.name).namedtuples())
        self.assertEqual(rows_nt[0].name, 'a')

    def test_mass_delete_and_cascade(self):
        i1 = Item.create(name='W', qty=1)
        t1 = Tag.create(name='x')
        t2 = Tag.create(name='y')
        ItemTag.create(item=i1, tag=t1)
        ItemTag.create(item=i1, tag=t2)
        self.assertEqual(ItemTag.select().count(), 2)

        # Deleting parent cascades to ItemTag (on_delete='CASCADE')
        i1.delete_instance(recursive=False)  # FK cascade should handle it
        self.assertFalse(Item.select().where(Item.name == 'W').exists())
        self.assertEqual(ItemTag.select().count(), 0)

    def test_expression_update(self):
        i = Item.create(name='counter', qty=5)
        (Item
         .update(qty=Item.qty + 3)
         .where(Item.id == i.id)
         .execute())
        self.assertEqual(Item.get_by_id(i.id).qty, 8)

    def test_transactions_atomic_and_rollback(self):
        start = Item.select().count()
        try:
            with db.atomic():
                Item.create(name='will_rollback', qty=1)
                # Force an IntegrityError by duplicating unique Tag
                Tag.create(name='unique_tag')
                Tag.create(name='unique_tag')  # boom
        except IntegrityError:
            pass
        # Item create should NOT have been committed due to rollback.
        self.assertEqual(Item.select().count(), start)

    def test_nested_atomic_savepoints(self):
        Item.create(name='A', qty=1)
        with db.atomic() as outer:
            Item.create(name='B', qty=2)
            try:
                with db.atomic() as inner:
                    Item.create(name='C', qty=3)
                    raise ValueError('force rollback inner')
            except ValueError:
                pass
            # Outer still active; A and B should exist, C should not.
            self.assertTrue(Item.select().where(Item.name == 'A').exists())
            self.assertTrue(Item.select().where(Item.name == 'B').exists())
            self.assertFalse(Item.select().where(Item.name == 'C').exists())

    def test_limit_offset_distinct_paginate(self):
        # Clear and add predictable items
        Item.delete().execute()
        for i in range(10):
            Item.create(name=f'p{i%3}', qty=i)

        distinct_names = [r.name for r in Item.select(Item.name).distinct().order_by(Item.name)]
        self.assertEqual(distinct_names, ['p0', 'p1', 'p2'])

        page1 = [r.qty for r in Item.select().order_by(Item.qty).paginate(1, 3)]
        page2 = [r.qty for r in Item.select().order_by(Item.qty).paginate(2, 3)]
        self.assertEqual(page1, [0, 1, 2])
        self.assertEqual(page2, [3, 4, 5])

    def test_contains_startswith_in_isnull(self):
        Item.create(name='needle', qty=0)
        Item.create(name='NeedleCase', qty=0)
        Item.create(name='hay', qty=0)

        contains_need = [r.name for r in Item.select().where(Item.name.contains('eed'))]
        self.assertIn('needle', contains_need)

        starts_needle_case_insensitive = [r.name for r in Item.select().where(fn.Lower(Item.name).startswith('nee'))]
        self.assertTrue(any(n.lower().startswith('nee') for n in starts_needle_case_insensitive))

        in_filter = [r.name for r in Item.select().where(Item.name.in_(['needle', 'hay']))]
        self.assertEqual(sorted(in_filter), ['hay', 'needle'])

        # is null / not null
        class MaybeNull(BulkBase):
            note = CharField(null=True)
            class Meta:
                database = db
        db.create_tables([MaybeNull])
        try:
            MaybeNull.create(note=None)
            MaybeNull.create(note='x')
            nulls = MaybeNull.select().where(MaybeNull.note.is_null(True)).count()
            not_nulls = MaybeNull.select().where(MaybeNull.note.is_null(False)).count()
            self.assertEqual(nulls, 1)
            self.assertEqual(not_nulls, 1)
        finally:
            db.drop_tables([MaybeNull])

    def test_subquery_in_(self):
        # Items with a tag named 'red'
        i1 = Item.create(name='apple', qty=1)
        i2 = Item.create(name='brick', qty=1)
        red = Tag.create(name='red')
        blue = Tag.create(name='blue')
        ItemTag.create(item=i1, tag=red)
        ItemTag.create(item=i2, tag=blue)

        subq = (ItemTag
                .select(ItemTag.item)
                .join(Tag)
                .where(Tag.name == 'red'))
        red_items = [i.name for i in Item.select().where(Item.id.in_(subq))]
        self.assertEqual(red_items, ['apple'])


# ---------------------------------------------------------------------------
# Extra coverage: Self-referential FK & alias, multi-join switch
# ---------------------------------------------------------------------------
class TreeBase(Model):
    class Meta:
        database = db

class Node(TreeBase):
    name = CharField()
    parent = ForeignKeyField('self', null=True, backref='children', on_delete='CASCADE')

class SelfRefAndJoinsTests(unittest.TestCase):
    def setUp(self):
        db.connect(reuse_if_open=True)
        db.create_tables([Node])

        # Build a small tree:
        # root
        #  ├─ a
        #  │   └─ a1
        #  └─ b
        self.root = Node.create(name='root', parent=None)
        self.a = Node.create(name='a', parent=self.root)
        self.b = Node.create(name='b', parent=self.root)
        self.a1 = Node.create(name='a1', parent=self.a)

    def tearDown(self):
        db.drop_tables([Node])
        db.close()

    def test_self_join_with_alias(self):
        Parent = Node.alias()
        q = (Node
             .select(Node, Parent)
             .join(Parent, on=(Node.parent == Parent.id))
             .where(Node.parent.is_null(False))
             .order_by(Node.name))
        # Materialize to avoid leaving an open cursor if an assertion fails
        rows = [(r.name, r.parent.name) for r in list(q)]
        self.assertEqual(rows, [('a', 'root'), ('a1', 'a'), ('b', 'root')])

    def test_recursive_delete_cascade(self):
        # Deleting 'a' should delete 'a1' due to CASCADE
        self.a.delete_instance()
        names = [n.name for n in Node.select().order_by(Node.name)]
        self.assertEqual(names, ['b', 'root'])

    def test_switch_for_multi_joins(self):
        P = Node.alias()
        C = Node.alias()
        q = (Node
             .select(Node.name, P.name.alias('pname'), C.name.alias('cname'))
             .join(P, on=(Node.parent == P.id))
             .switch(Node)
             .join(C, JOIN.LEFT_OUTER, on=(C.parent == Node.id))
             .where(P.name == 'root')
             .order_by(Node.name, C.name)
             .tuples())
        rows = list(q)  # [('a','root','a1'), ('b','root',None)]
        self.assertEqual(rows, [
            ('a', 'root', 'a1'),
            ('b', 'root', None),
        ])


# ---------------------------------------------------------------------------
# Extra coverage: UUID PKs, callable defaults, date/time filtering
# ---------------------------------------------------------------------------
class UuidBase(Model):
    class Meta:
        database = db

class UThing(UuidBase):
    id = UUIDField(primary_key=True, default=uuid4)
    name = CharField()
    created = DateTimeField(default=lambda: datetime.now(timezone.utc))

class UUIDAndTemporalTests(unittest.TestCase):
    def setUp(self):
        db.connect(reuse_if_open=True)
        db.create_tables([UThing])

    def tearDown(self):
        db.drop_tables([UThing])
        db.close()

    def test_uuid_primary_key_and_defaults(self):
        u = UThing.create(name='u1')
        self.assertTrue(isinstance(u.id, type(uuid4())))
        self.assertTrue(isinstance(u.created, datetime))

    def test_datetime_filters(self):
        t1 = UThing.create(name='old', created=datetime(2020, 1, 1, tzinfo=timezone.utc))
        t2 = UThing.create(name='new', created=datetime(2030, 1, 1, tzinfo=timezone.utc))
        newer = [r.name for r in UThing.select().where(UThing.created > datetime(2025, 1, 1, tzinfo=timezone.utc))]
        self.assertEqual(newer, ['new'])


# ---------------------------------------------------------------------------
# Extra coverage: Aggregates, HAVING, multi-column order
# ---------------------------------------------------------------------------
class SalesBase(Model):
    class Meta:
        database = db

class Sale(SalesBase):
    sku = CharField()
    qty = IntegerField()
    region = CharField()

class AggregatesAndHavingTests(unittest.TestCase):
    def setUp(self):
        db.connect(reuse_if_open=True)
        db.create_tables([Sale])
        rows = [
            {'sku': 'A', 'qty': 1, 'region': 'EU'},
            {'sku': 'A', 'qty': 2, 'region': 'US'},
            {'sku': 'B', 'qty': 10, 'region': 'EU'},
            {'sku': 'B', 'qty': 5, 'region': 'US'},
            {'sku': 'C', 'qty': 1, 'region': 'EU'},
        ]
        Sale.insert_many(rows).execute()

    def tearDown(self):
        db.drop_tables([Sale])
        db.close()

    def test_group_by_and_having(self):
        q = (Sale
             .select(Sale.sku, fn.SUM(Sale.qty).alias('t'))
             .group_by(Sale.sku)
             .having(fn.SUM(Sale.qty) > 3)
             .order_by(Sale.sku))
        got = [(r.sku, r.t) for r in list(q)]
        self.assertEqual(got, [('B', 15)])

    def test_multi_column_order(self):
        q = (Sale
             .select()
             .order_by(Sale.region.asc(), Sale.qty.desc()))
        first = [(r.region, r.qty, r.sku) for r in list(q)[:3]]
        # EU rows come first, highest qty first for EU
        self.assertTrue(first[0][0] <= first[1][0] <= first[2][0])


# ---------------------------------------------------------------------------
# Extra coverage: Raw SQL
# ---------------------------------------------------------------------------
class RawSQLTests(unittest.TestCase):
    def setUp(self):
        db.connect(reuse_if_open=True)

    def tearDown(self):
        db.close()

    def test_simple_execute_sql(self):
        cur = db.execute_sql('SELECT 1')
        row = cur.fetchone()
        self.assertEqual(row[0], 1)


if __name__ == '__main__':
    unittest.main()