from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import datetime
from ItemCatalog import Category, CategoryItem, Base, User

engn = create_engine('sqlite:///ItemCatalog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance

# Clear database
Base.metadata.drop_all(engn)
Base.metadata.create_all(engn)

Session = sessionmaker(bind=engn)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = Session()

# Create dummy user
user1 = User(
    name="Robo Barista",
    email="tinnyTim@udacity.com",
    picture='https://pbs.twimg.com/profile_images'
    '/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(user1)
session.commit()

category1 = Category(
    user=user1,
    name='Snowboarding'
)

session.add(category1)
session.commit()

item1 = CategoryItem(
    name='Snowboard',
    detail='Best for any terrain and conditions. '
    'All mountain snowboards perform anywhere on a mountain-groomed '
    'runs, backcountry, even park and pipe.',
    category=category1,
    user=user1
)

session.add(item1)
session.commit()

item2 = CategoryItem(
    name='Goggles',
    detail='Best for any terrain and conditions. '
    'All mountain goggles perform anywhere on a mountain-groomed '
    'runs, backcountry, even park and pipe.',
    category=category1,
    user=user1
)

session.add(item2)
session.commit()

category2 = Category(
    user=user1,
    name='Soccer'
)

session.add(category2)
session.commit()

item3 = CategoryItem(
    name='Two shinguards',
    detail='Best for any terrain and conditions. '
    'All mountain Two shinguards perform anywhere on '
    'a mountain-groomed runs, backcountry, even park and pipe.',
    category=category2,
    user=user1
)

session.add(item3)
session.commit()

item4 = CategoryItem(
    name='Shinguards',
    detail='Best for any terrain and conditions. '
    'All mountain Shinguards perform anywhere on a '
    'mountain-groomed runs, backcountry, even park and pipe.',
    category=category2,
    user=user1
)

session.add(item4)
session.commit()

item5 = CategoryItem(
    name='Jersey',
    detail='Best for any terrain and conditions. '
    'All mountain Jersey perform anywhere on a mountain-groomed'
    'runs, backcountry, even park and pipe.',
    category=category2,
    user=user1
)

session.add(item5)
session.commit()

item6 = CategoryItem(
    name='Soccer Cleats',
    detail='Best for any terrain and conditions. '
    'All mountain Soccer Cleats perform anywhere on '
    'a mountain-groomed runs, backcountry, even park and pipe.',
    category=category2,
    user=user1
)

session.add(item6)
session.commit()

print("added itemCatalog categories & items!")
