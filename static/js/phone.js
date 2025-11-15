    function phoneComponent(conversationData) {
      return {
        conversation: conversationData,
        messages: [],
        isPlaying: false,

        playOnEnter() {
            window.addEventListener('scroll', () => {
                const rect = this.$el.getBoundingClientRect();
                if (rect.bottom < window.innerHeight+100 && rect.top > -600) { this.play() }
            })
        },

        scrollToBottom() {
           const container = this.$el.querySelector('.chat-container');
            if (container) {
            const observer = new MutationObserver(() => {
                requestAnimationFrame(() => {
                container.scrollTo({
                    top: container.scrollHeight,
                    behavior: 'smooth'
                });
                });
            });
            observer.observe(container, { childList: true, subtree: true });
          }
        },

        play() {
          let i = 0;
          const addMessage = () => {
            if (this.messages.length === this.conversation.length) {
              this.messages = [];
              i = 0;
            }
            if (i < this.conversation.length) {
              this.messages.push(this.conversation[i]);
               this.scrollToBottom();

              const cooldown = this.conversation[i].cooldown || 1000;
              i++;
              setTimeout(addMessage, cooldown);
            }

          };
          
          if (!this.isPlaying) {
            addMessage();
            
            this.isPlaying = true;

            this.$nextTick(() => {
               this.scrollToBottom();
            });
          }
        },

        renderPhone() {
          return `
            <div class="relative w-[290px] h-[586px]">
              <img src="/static/img/assets/iphone.png" alt="iphone frame" draggable="false" class="absolute z-10 top-0 left-0 w-[290px] object-contain select-none" />


              <div class="phone absolute top-[26px] left-[20px] rounded-[40px] w-[250px] h-[540px] overflow-hidden bg-white flex flex-col">
                
                <!-- Header -->
                <div class="header">
                    <img src="/static/img/assets/header.svg" alt="message ui header">
                </div>

                <!-- Messages -->
                <div class="chat-container flex-1 overflow-y-auto scrollbar-hidden flex flex-col">
                  <div class="p-4 pt-[380px] flex flex-col w-full">
                    <template x-for="(msg, msgIndex) in messages" :key="msgIndex">
                      <div class="relative w-full">
                        
                        <!-- Text message -->
                        <template x-if="msg.type === 'text'">
                          <div class="msg max-w-[70%]" :class="msg.role" x-text="msg.content"></div>
                        </template>

                        <!-- Image message -->
                        <template x-if="msg.type === 'image'">
                          <div :class="msg.role" class="msg p-0 w-[70%] overflow-hidden border border-gray-200">
                            <img :src="msg.content" alt="Image" class="w-full">
                          </div>
                        </template>

                        <template x-if="msg.type === 'voice'">
                          <div :class="msg.role" class="msg px-2.5 py-4 w-[70%] overflow-hidden bg-gray-200 text-gray-800">
                              <div class="flex items-center justify-between gap-2">
                                  <div class="flex items-center gap-2">
                                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-play-icon lucide-play"><path d="M5 5a2 2 0 0 1 3.008-1.728l11.997 6.998a2 2 0 0 1 .003 3.458l-12 7A2 2 0 0 1 5 19z"/></svg>
                                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-audio-lines-icon lucide-audio-lines"><path d="M2 10v3"/><path d="M6 6v11"/><path d="M10 3v18"/><path d="M14 8v7"/><path d="M18 5v13"/><path d="M22 10v3"/></svg>
                                  </div>
                                  <span class="text-xs text-gray-500"" x-text="msg.duration"></span>
                              </div>
                          </div>
                        </template>

                        <!-- Products carousel -->
                        <template x-if="msg.type === 'products'">
                          <div class="msg product-bubble  p-0 !bg-white inline-block" :class="msg.role" 
                               x-data="{
                                 scrollToCard(dir) {
                                   const container = $el.querySelector('.products');
                                   if (!container) return;
                                   const card = container.querySelector('.product-card');
                                   const cardWidth = card ? card.offsetWidth : container.clientWidth;
                                   requestAnimationFrame(() => {
                                     container.scrollBy({ left: dir * cardWidth, behavior: 'smooth' });
                                   });
                                 },
                                 canScroll(dir) {
                                   const container = $el.querySelector('.products');
                                   if (!container) return false;
                                   if (dir > 0) return container.scrollLeft + container.clientWidth < container.scrollWidth - 1;
                                   return container.scrollLeft > 0;
                                 }
                               }">
                            <div class="relative" x-init="let count = 0; setInterval(() => {
                              if (count < 1) count++;
                                scrollToCard(1);
                              if (count === 2) clearInterval(this);
                            }, 800);">
                              <div class="products scrollbar-hidden w-[150px] flex overflow-x-auto p-0 border border-gray-100 rounded-xl">
                                <template x-for="(item, idx) in msg.content" :key="idx">
                                  <div class="w-[150px] flex-shrink-0 product-card bg-white overflow-hidden shadow-sm">
                                    <div class="relative w-full aspect-square bg-white flex items-center justify-center">
                                      <img :src="item.image" :alt="item.title" class="w-full aspect-square object-contain">
                                    </div>
                                    <div class="bg-gray-100 p-2.5">
                                      <div class="font-medium text-[13px]" x-text="item.title"></div>
                                      <div class="text-[11px] text-gray-600" x-text="item.subtitle"></div>
                                      <div class="flex gap-2 mt-2">
                                        <button class="bg-gray-200 py-1 px-2.5 flex-1 text-center rounded-md text-xs">Buy</button>
                                        <button class="bg-gray-200 py-1 px-2.5 flex-1 text-center rounded-md text-xs">View</button>
                                      </div>
                                    </div>
                                  </div>
                                </template>
                              </div>

                              <!-- Navigation buttons -->
                              <div class="absolute top-1/2 -translate-y-1/2 -right-3">
                                <button @click="scrollToCard(1)" class="p-1 bg-white rounded-full shadow-md border border-gray-200">
                                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m9 18 6-6-6-6"/></svg>
                                </button>
                              </div>
                              <div class="absolute top-1/2 -translate-y-1/2 -left-3">
                                <button @click="scrollToCard(-1)" class="p-1 bg-white rounded-full shadow-md border border-gray-200">
                                  <svg class="rotate-180" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m9 18 6-6-6-6"/></svg>
                                </button>
                              </div>
                            </div>
                          </div>
                        </template>

                        <!-- Quick replies -->
                        <template x-if="msg.type === 'replies'">
                          <div class="!bg-white msg w-full flex gap-2 flex-wrap" :class="msg.role" x-init="setTimeout(() => $el.classList.add('hidden'), msg.cooldown)">
                            <template x-for="(reply, rIndex) in msg.content" :key="rIndex">
                              <button class="bg-[#0584FE] text-white text-[12px] px-2.5 py-1 rounded-full whitespace-nowrap" x-text="reply"></button>
                            </template>
                          </div>
                        </template>

                        <!-- Receipt -->
                        <template x-if="msg.type === 'receipt'">
                          <div class="msg w-[70%]" :class="msg.role">
                            <div class="flex">
                              <div class="w-6 h-6 p-1 bg-neutral-400 flex items-center justify-center rounded-full">
                                <div class="p-0.5 bg-white rounded-full">
                                  <svg class="stroke-neutral-400" xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M20 6 9 17l-5-5"/></svg>
                                </div>
                              </div>
                              <div class="ml-2">
                                <div class="font-medium text-sm mb-1">Order Confirmation</div>
                                <div class="text-xs text-gray-600" x-text="msg.content"></div>
                              </div>
                            </div>
                          </div>
                        </template>

                      </div>
                    </template>
                  </div>
                </div>

                <!-- Footer -->
                <div class="footer">
                    <img src="/static/img/assets/footer.svg" alt="message input footer">
                    <div class="block h-[3px] w-22 rounded bg-gray-800 mx-auto mt-4 mb-2"></div>
                </div>
              </div>
            </div>
          `;
        }
      }
    }