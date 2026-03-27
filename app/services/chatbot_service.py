import os
import json
from datetime import datetime
from openai import OpenAI
from app.config.database import db

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ChatbotService:
    @staticmethod
    def get_response(message, user_id=None):
        message = message.lower().strip()
        
        # 0. Show All Capabilities if asked "what can you do"
        if any(word in message for word in ["help", "what can you do", "features", "capabilities"]):
            return {
                "response": "🤖 **I am HostelPro Assistant!**\n\nI can help you with:\n• **Mess Menu** 🍽 (Today's breakfast, lunch, dinner)\n• **WiFi Info** 📶 (Passwords for your floor)\n• **Laundry** 🧺 (Booking instructions)\n• **Tickets** 🎫 (How to raise complaints)\n• **Notices** 📢 (Latest hostel updates)\n• **Profile/Fees** 🏠 (Room & payment details)\n\nJust ask me anything!"
            }

        # 1. Mess / Food Menu
        if any(word in message for word in ["food", "menu", "lunch", "breakfast", "dinner", "eat"]):
            return ChatbotService._get_mess_menu(message)
            
        # 2. WiFi
        if "wifi" in message or "internet" in message or "password" in message:
            return ChatbotService._get_wifi_info(message)
            
        # 3. Laundry
        if "laundry" in message or "washing machine" in message:
            return {
                "response": "🧺 **Laundry / Washing Machine**\n\nYou can book a washing machine from the Laundry Booking section.\n\n**Steps:**\n1. Open **Laundry Module**\n2. Select an available time slot\n3. Confirm your booking\n\nTimings: 6:00 AM - 10:00 PM"
            }
            
        # 4. Complaint / Ticket
        if any(word in message for word in ["complaint", "issue", "problem", "ticket", "not working", "electric", "water"]):
            return {
                "response": "🎫 **Complaint / Ticket System**\n\nYou can create a complaint ticket for any issues like WiFi, water, or electricity.\n\n**Steps:**\n1. Go to **Ticket Section**\n2. Click **Create Ticket**\n3. Select issue type (e.g., Maintenance, Food)\n4. Submit your details\n\nOur team will resolve it soon!"
            }
            
        # 5. Announcements / Notices
        if any(word in message for word in ["announcement", "notice", "update", "latest"]):
            return ChatbotService._get_announcements()
            
        # 6. Room Info
        if any(word in message for word in ["room", "roommate", "where do i live"]):
            return ChatbotService._get_room_info(user_id)
            
        # 7. Fee
        if any(word in message for word in ["fee", "due", "payment", "paid", "balance", "money"]):
            return ChatbotService._get_fee_info(user_id)
            
        # 8. Emergency
        if any(word in message for word in ["emergency", "help", "security", "warden", "police"]):
            return {
                "response": "🚨 **Emergency Alert**\n\nPlease contact the following immediately if you need help:\n\n• **Hostel Manager:** +91 XXXXXXXX\n• **Security Desk:** +91 XXXXXXXX\n• **Warden Desk:** +91 XXXXXXXX\n\nStay safe!"
            }

        # Use OpenAI for dynamic responses if no keywords match prominently
        try:
            prompt_context = "You are 'HostelPro Assistant', a premium and polite chatbot for a hostel management system. Respond concisely."
            if not user_id:
                prompt_context += " Note: The user is not currently logged in, so you cannot see their personal room or fee details. Ask them to log in if they ask about 'my room' or 'my fees'."
            else:
                prompt_context += " The user is logged in. If they ask about personal room/fees, tell them they can find it in the Profile/Payments section."

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": prompt_context},
                    {"role": "user", "content": message}
                ],
                max_tokens=150
            )
            return {"response": response.choices[0].message.content}
        except Exception as e:
            return {
                "response": "Sorry, I didn't understand that.\n\n**You can ask about:**\n• Mess menu 🍽\n• WiFi Information 📶\n• Laundry Booking 🧺\n• Complaints / Tickets 🎫\n• Latest Announcements 📢\n• Your Room & Fees 🏠"
            }

    @staticmethod
    def _get_mess_menu(message):
        try:
            # Check for specific day in query
            days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturady", "sunday"]
            target_day = None
            for d in days:
                if d in message:
                    target_day = d.capitalize()
                    break
            
            # If "tomorrow", calculate it
            if "tomorrow" in message:
                import datetime as dt
                target_day = (dt.date.today() + dt.timedelta(days=1)).strftime("%A")

            # Default to today
            if not target_day:
                target_day = datetime.now().strftime("%A")

            menu_data = db["food_menu"].find_one({"day": target_day})
            
            if menu_data and "menu" in menu_data:
                m = menu_data["menu"]
                return {
                    "response": f"🍽 **Menu for {target_day}**\n\n**Breakfast:** {m.get('breakfast', 'N/A')}\n**Lunch:** {m.get('lunch', 'N/A')}\n**Dinner:** {m.get('dinner', 'N/A')}\n\n*Mess Timings: 7:30 AM - 9:30 PM*"
                }
            
            # If specific day asked but not found
            if any(d in message for d in days) or "tomorrow" in message:
                return {"response": f"🍽 **Mess Menu**\n\nMenu for {target_day} has not been updated yet by the admin."}

            # Fallback: List all available days summary
            all_menus = list(db["food_menu"].find())
            if all_menus:
                days_list = ", ".join([mn.get("day") for mn in all_menus])
                return {
                    "response": f"🍽 **Mess Menu**\n\nToday ({target_day}) is not updated, but I have menus for: **{days_list}**.\n\nWhich one would you like to see?"
                }

            return {
                "response": "🍽 **Mess Menu**\n\nToday's menu details haven't been updated by the admin yet.\n\n**Standard Timings:**\nBreakfast: 7:30 - 9:30 AM\nLunch: 12:30 - 2:30 PM\nDinner: 7:30 - 9:30 PM"
            }
        except Exception as e:
            return {"response": f"I'm having trouble fetching the Mess Menu right now. Please check the **Mess Menu** section."}

    @staticmethod
    def _get_wifi_info(message):
        try:
            # Check for floor specific queries (handles "1st", "floor 1", "2nd" etc)
            import re
            floor_match = re.search(r'(\d+)', message)
            floor = floor_match.group(1) if floor_match else None
            
            query = {}
            if floor:
                # Query with both string and int just in case
                query["$or"] = [{"floor": str(floor)}, {"floor": int(floor)}]
            
            wifis = list(db["wifi_configs"].find(query))
            
            if wifis:
                resp = "📶 **WiFi Information**\n\n"
                for wifi in wifis:
                    resp += f"• **SSID:** {wifi.get('ssid', 'N/A')}\n"
                    resp += f"  **Password:** `{wifi.get('password', 'N/A')}`\n"
                    if wifi.get('floor'): resp += f"  **Floor:** {wifi.get('floor')}\n"
                    if wifi.get('speed'): resp += f"  **Speed:** {wifi.get('speed')}\n"
                    resp += "\n"
                return {"response": resp.strip()}
            
            return {
                "response": "📶 **WiFi Information**\n\nI couldn't find specific WiFi details for your query.\n\n**General Network:** Hostel_Main\n**Password:** `hostel@123`\n\nFor more floor-specific passwords, check the **WiFi Credentials** section."
            }
        except:
            return {"response": "WiFi details are unavailable at the moment. Please contact the warden."}

    @staticmethod
    def _get_announcements():
        try:
            notices = list(db["notices"].find().sort("created_at", -1).limit(3))
            if notices:
                resp = "📢 **Latest Announcements**\n\n"
                for n in notices:
                    resp += f"• **{n.get('title')}**\n{n.get('content')}\n\n"
                return {"response": resp.strip()}
            return {"response": "📢 **No recent announcements.** Everything is running smoothly!"}
        except:
            return {"response": "Could not fetch announcements. Please check the **Notice Board**."}

    @staticmethod
    def _get_room_info(user_id):
        if not user_id:
            return {"response": "🏠 **Room Information**\n\nPlease log in to see your personal room number and roommate details."}
        try:
            student = db["students"].find_one({"user_id": user_id})
            if student and student.get("room_number"):
                room_number = student.get("room_number")
                roommates = list(db["students"].find({"room_number": room_number, "user_id": {"$ne": user_id}}))
                roommate_names = ", ".join([r.get("name", "N/A") for r in roommates]) if roommates else "None"
                
                return {
                    "response": f"🏠 **Your Room Details**\n\n**Room No:** {room_number}\n**Bed No:** {student.get('bed_number', 'N/A')}\n**Roommate(s):** {roommate_names}"
                }
            return {"response": "🏠 **Room Information**\n\nYou haven't been allocated a room yet. Please contact the administrator."}
        except:
            return {"response": "Error fetching your room details. Check your **Profile**."}

    @staticmethod
    def _get_fee_info(user_id):
        if not user_id:
            return {"response": "💰 **Fee Information**\n\nPlease log in to view your payment status and dues."}
        try:
            payment = db["payments"].find_one({"student_id": str(user_id)}, sort=[("created_at", -1)])
            if not payment:
                from bson import ObjectId
                if ObjectId.is_valid(str(user_id)):
                    payment = db["payments"].find_one({"student_id": ObjectId(user_id)}, sort=[("created_at", -1)])

            if payment:
                return {
                    "response": f"💰 **Hostel Fee Details**\n\n**Total Amount:** ₹{payment.get('amount', 0)}\n**Paid:** ₹{payment.get('amount_paid', 0)}\n**Remaining:** ₹{payment.get('balance', 0)}\n**Status:** {payment.get('status', 'N/A').upper()}"
                }
            return {"response": "💰 **Fee Information**\n\nNo payment records found for your account. Check the **Payments** section for more info."}
        except:
            return {"response": "Could not retrieve fee information at this time."}
