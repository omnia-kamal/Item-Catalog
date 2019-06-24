from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime
from Database import *

engine = create_engine('sqlite:///Catalog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)


session = DBSession()
#Clear Database
session.query(Category).delete()
session.query(CategoryItem).delete()
session.query(User).delete()

#Populating Database Tables
User1 = User(name="Omnia kamal", email="nbaynom0@skype.com")
session.add(User1)
session.commit()


# Create fake categories
Category1 = Category(name="Soccer",
                      user_id=1)
session.add(Category1)
session.commit()

Category2 = Category(name="Basketball",
                      user_id=2)
session.add(Category2)
session.commit

Category3 = Category(name="Baseball",
                      user_id=1)
session.add(Category3)
session.commit()

Category4 = Category(name="Frisbee",
                      user_id=1)
session.add(Category4)
session.commit()

Category5 = Category(name="Snowboarding",
                      user_id=1)
session.add(Category5)
session.commit()

Category6 = Category(name="Rockclimbing",
                      user_id=1)
session.add(Category6)
session.commit()

Category7 = Category(name="Foosball",
                      user_id=1)
session.add(Category7)
session.commit()

Category8 = Category(name="Skating",
                      user_id=1)
session.add(Category8)
session.commit()

Category9 = Category(name="Hockey",
                      user_id=1)
session.add(Category9)
session.commit()


Item1 = CategoryItem(name="Ball",
               description="Essential for Soccer",
               category_id=1,
               user_id=1)
session.add(Item1)
session.commit()

Item2 = CategoryItem(name="Shirt",
               description="Shirt to play Soccer",
              
               category_id=1,
               user_id=1)
session.add(Item2)
session.commit()


print ("Items Added")