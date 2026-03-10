"""
SmartBill User Creation Script
Run this in Django shell: python manage.py shell < create_users_script.py
"""

from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from bills.models import Bill, Budget

# Create Groups
admin_group, _ = Group.objects.get_or_create(name='Admin')
manager_group, _ = Group.objects.get_or_create(name='Finance Manager')
executive_group, _ = Group.objects.get_or_create(name='Finance Executive')

# Get content types
bill_ct = ContentType.objects.get_for_model(Bill)
budget_ct = ContentType.objects.get_for_model(Budget)

# Admin - Full permissions
admin_permissions = Permission.objects.filter(
    content_type__in=[bill_ct, budget_ct]
)
admin_group.permissions.set(admin_permissions)

# Finance Manager - Can view, add, change (no delete)
manager_permissions = Permission.objects.filter(
    content_type__in=[bill_ct, budget_ct],
    codename__in=['view_bill', 'add_bill', 'change_bill', 
                  'view_budget', 'add_budget', 'change_budget']
)
manager_group.permissions.set(manager_permissions)

# Finance Executive - Can only view and add
executive_permissions = Permission.objects.filter(
    content_type__in=[bill_ct, budget_ct],
    codename__in=['view_bill', 'add_bill', 'view_budget', 'add_budget']
)
executive_group.permissions.set(executive_permissions)

# Create Users
users_to_create = [
    {
        'username': 'admin',
        'password': 'admin123',
        'email': 'admin@smartbill.com',
        'first_name': 'System',
        'last_name': 'Admin',
        'group': admin_group,
        'is_staff': True,
        'is_superuser': True
    },
    {
        'username': 'finance_manager',
        'password': 'manager123',
        'email': 'manager@smartbill.com',
        'first_name': 'Finance',
        'last_name': 'Manager',
        'group': manager_group,
        'is_staff': True,
        'is_superuser': False
    },
    {
        'username': 'finance_executive',
        'password': 'executive123',
        'email': 'executive@smartbill.com',
        'first_name': 'Finance',
        'last_name': 'Executive',
        'group': executive_group,
        'is_staff': False,
        'is_superuser': False
    }
]

print("Creating users...")
print("="*60)

for user_data in users_to_create:
    username = user_data['username']
    
    # Check if user exists
    if User.objects.filter(username=username).exists():
        print(f"⚠️  User '{username}' already exists. Skipping...")
        continue
    
    # Create user
    user = User.objects.create_user(
        username=user_data['username'],
        password=user_data['password'],
        email=user_data['email'],
        first_name=user_data['first_name'],
        last_name=user_data['last_name'],
        is_staff=user_data['is_staff'],
        is_superuser=user_data['is_superuser']
    )
    
    # Add to group
    user.groups.add(user_data['group'])
    
    print(f"✅ Created: {username}")
    print(f"   Email: {user_data['email']}")
    print(f"   Password: {user_data['password']}")
    print(f"   Role: {user_data['group'].name}")
    print()

print("="*60)
print("✅ User creation complete!")
print()
print("LOGIN CREDENTIALS:")
print("-"*60)
print("1. ADMIN:")
print("   Username: admin")
print("   Password: admin123")
print("   Role: Full access to everything")
print()
print("2. FINANCE MANAGER:")
print("   Username: finance_manager")
print("   Password: manager123")
print("   Role: Can view, add, edit (no delete)")
print()
print("3. FINANCE EXECUTIVE:")
print("   Username: finance_executive")
print("   Password: executive123")
print("   Role: Can view and add only")
print("="*60)
