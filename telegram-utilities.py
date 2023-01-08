from pyrogram import Client
from pyrogram.enums import ChatMemberStatus
from pyrogram.raw import functions


api_id = 0
api_hash = ""

# takeout session has less restrictions. not sure if there are any drawbacks though
app = Client("my_account", api_id, api_hash, takeout=True)

target_chat_id = -0


# helper function
async def get_msg_contents(msg):
	# this is so ugly
	contents = (
		msg.text
		or list(filter(None, (msg.media, msg.caption)))
		or getattr(msg.service, "value", None)
	)
	return contents


async def delete_all_my_msgs(target_chat_id):
	target_user_id = "me"

	target_chat = await app.get_chat(target_chat_id)
	print("Chat:", target_chat.title, target_chat.type)

	msg_count = await app.search_messages_count(
		chat_id=target_chat_id, from_user=target_user_id
	)
	print(f"Messages found: {msg_count}")

	# user_id can also be the string "self"
	member = await app.get_chat_member(target_chat_id, target_user_id)
	print(f"Chat permissions: {member.status}")
	has_sufficient_perms = (
		member.status == ChatMemberStatus.ADMINISTRATOR
		or member.status == ChatMemberStatus.OWNER
	)

	if has_sufficient_perms:
		# method 1
		if await app.delete_user_history(
			chat_id=target_chat_id, user_id=target_user_id
		):
			print("History deleted")
		else:
			print("History deletion failed")

	# method 2:
	async for msg in app.search_messages(
		chat_id=target_chat_id, from_user=target_user_id
	):
		contents = await get_msg_contents(msg)

		# Message.delete() is essentially a shortcut for await app.delete_messages(chat_id, message_id)
		# though, advantage of delete_messages() is that message_id can be a list
		if await msg.delete(revoke=True):
			print("Message deleted:", contents)
		else:
			print("Message deletion failed:", contents)

	# print("Checking for any messages remaining...")

	# # method 3: slowest probably
	# async for msg in app.get_chat_history(target_chat_id):
	# 	if msg.from_user and msg.from_user.id == "me":
	# 		print("Remaining message:", msg.text)

	print("Done!")


async def get_left_channels():
	chats = await app.invoke(functions.channels.GetLeftChannels(offset=0))

	chats = chats.chats
	for chat in chats:
		# chat.QUALNAME is types.Channel and chat.left is True
		print((chat.id, chat.title, getattr(chat, "username", None)))

	return chats


async def get_joined_chats():

	chats = await app.invoke(functions.messages.GetAllChats(except_ids=[]))

	chats = chats.chats
	for chat in chats:
		# chat.QUALNAME can be multiple types and chat.left is False
		print((chat.id, chat.title, getattr(chat, "username", None)))

	return chats


# note that groups can now hide their member list
async def get_common_members(target_chat_ids):
	if not target_chat_ids:
		return

	member_lists = []
	for target_chat_id in target_chat_ids:
		members = []
		async for member in app.get_chat_members(target_chat_id):
			members.append(member.user.id)
		member_lists.append(members)

	# https://stackoverflow.com/questions/3852780/python-intersection-of-multiple-lists
	# common_members = set(member_lists[0]).intersection(*member_lists[1:])
	# common_members = set.intersection(*map(set, member_lists))
	common_members = set(member_lists.pop()).intersection(*member_lists)

	users = await app.get_users(common_members)
	users_info = [
		(user.id, user.username, user.first_name, user.last_name) for user in users
	]

	print("Common members:")
	for user_info in users_info:
		print(user_info)

	return users


async def main():
	async with app:
		me = await app.get_me()
		my_id = me.id

		print("Checking restrictions:", (me.is_restricted, me.is_scam, me.is_fake))

		# await get_common_members(target_chat_ids=[])

		# await delete_all_my_msgs(target_chat_id)

		# await get_left_channels()

    
# alternative: import asyncio; asyncio.run(main())
# https://docs.pyrogram.org/start/invoking#using-asyncio-run
app.run(main())
