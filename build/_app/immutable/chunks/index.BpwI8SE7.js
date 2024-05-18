var C=Object.defineProperty;var j=(e,t,n)=>t in e?C(e,t,{enumerable:!0,configurable:!0,writable:!0,value:n}):e[t]=n;var $=(e,t,n)=>(j(e,typeof t!="symbol"?t+"":t,n),n);import{r as h,n as y,f as w,h as B,i as S,j as I,k as b,l as L,m as q,p as N,q as P,v as T,w as D}from"./scheduler.BeaK0CkN.js";let p=!1;function H(){p=!0}function M(){p=!1}function O(e,t,n,i){for(;e<t;){const s=e+(t-e>>1);n(s)<=i?e=s+1:t=s}return e}function z(e){if(e.hydrate_init)return;e.hydrate_init=!0;let t=e.childNodes;if(e.nodeName==="HEAD"){const r=[];for(let l=0;l<t.length;l++){const o=t[l];o.claim_order!==void 0&&r.push(o)}t=r}const n=new Int32Array(t.length+1),i=new Int32Array(t.length);n[0]=-1;let s=0;for(let r=0;r<t.length;r++){const l=t[r].claim_order,o=(s>0&&t[n[s]].claim_order<=l?s+1:O(1,s,d=>t[n[d]].claim_order,l))-1;i[r]=n[o]+1;const f=o+1;n[f]=r,s=Math.max(f,s)}const c=[],a=[];let u=t.length-1;for(let r=n[s]+1;r!=0;r=i[r-1]){for(c.push(t[r-1]);u>=r;u--)a.push(t[u]);u--}for(;u>=0;u--)a.push(t[u]);c.reverse(),a.sort((r,l)=>r.claim_order-l.claim_order);for(let r=0,l=0;r<a.length;r++){for(;l<c.length&&a[r].claim_order>=c[l].claim_order;)l++;const o=l<c.length?c[l]:null;e.insertBefore(a[r],o)}}function F(e,t){if(p){for(z(e),(e.actual_end_child===void 0||e.actual_end_child!==null&&e.actual_end_child.parentNode!==e)&&(e.actual_end_child=e.firstChild);e.actual_end_child!==null&&e.actual_end_child.claim_order===void 0;)e.actual_end_child=e.actual_end_child.nextSibling;t!==e.actual_end_child?(t.claim_order!==void 0||t.parentNode!==e)&&e.insertBefore(t,e.actual_end_child):e.actual_end_child=t.nextSibling}else(t.parentNode!==e||t.nextSibling!==null)&&e.appendChild(t)}function te(e,t,n){p&&!n?F(e,t):(t.parentNode!==e||t.nextSibling!=n)&&e.insertBefore(t,n||null)}function G(e){e.parentNode&&e.parentNode.removeChild(e)}function R(e){return document.createElement(e)}function U(e){return document.createElementNS("http://www.w3.org/2000/svg",e)}function x(e){return document.createTextNode(e)}function ne(){return x(" ")}function ie(){return x("")}function re(e,t,n,i){return e.addEventListener(t,n,i),()=>e.removeEventListener(t,n,i)}function se(e,t,n){n==null?e.removeAttribute(t):e.getAttribute(t)!==n&&e.setAttribute(t,n)}function le(e){return e.dataset.svelteH}function ae(e){return e===""?null:+e}function V(e){return Array.from(e.childNodes)}function W(e){e.claim_info===void 0&&(e.claim_info={last_index:0,total_claimed:0})}function E(e,t,n,i,s=!1){W(e);const c=(()=>{for(let a=e.claim_info.last_index;a<e.length;a++){const u=e[a];if(t(u)){const r=n(u);return r===void 0?e.splice(a,1):e[a]=r,s||(e.claim_info.last_index=a),u}}for(let a=e.claim_info.last_index-1;a>=0;a--){const u=e[a];if(t(u)){const r=n(u);return r===void 0?e.splice(a,1):e[a]=r,s?r===void 0&&e.claim_info.last_index--:e.claim_info.last_index=a,u}}return i()})();return c.claim_order=e.claim_info.total_claimed,e.claim_info.total_claimed+=1,c}function A(e,t,n,i){return E(e,s=>s.nodeName===t,s=>{const c=[];for(let a=0;a<s.attributes.length;a++){const u=s.attributes[a];n[u.name]||c.push(u.name)}c.forEach(a=>s.removeAttribute(a))},()=>i(t))}function ue(e,t,n){return A(e,t,n,R)}function ce(e,t,n){return A(e,t,n,U)}function J(e,t){return E(e,n=>n.nodeType===3,n=>{const i=""+t;if(n.data.startsWith(i)){if(n.data.length!==i.length)return n.splitText(i.length)}else n.data=i},()=>x(t),!0)}function fe(e){return J(e," ")}function oe(e,t){t=""+t,e.data!==t&&(e.data=t)}function _e(e,t){e.value=t??""}function de(e,t,n,i){n==null?e.style.removeProperty(t):e.style.setProperty(t,n,"")}function me(e,t,n){for(let i=0;i<e.options.length;i+=1){const s=e.options[i];if(s.__value===t){s.selected=!0;return}}(!n||t!==void 0)&&(e.selectedIndex=-1)}function he(e){const t=e.querySelector(":checked");return t&&t.__value}function pe(e,t,n){e.classList.toggle(t,!!n)}function $e(e,t){return new e(t)}const m=new Set;let _;function ye(){_={r:0,c:[],p:_}}function xe(){_.r||h(_.c),_=_.p}function K(e,t){e&&e.i&&(m.delete(e),e.i(t))}function ge(e,t,n,i){if(e&&e.o){if(m.has(e))return;m.add(e),_.c.push(()=>{m.delete(e),i&&(n&&e.d(1),i())}),e.o(t)}else i&&i()}function ve(e){e&&e.c()}function we(e,t){e&&e.l(t)}function Q(e,t,n){const{fragment:i,after_update:s}=e.$$;i&&i.m(t,n),b(()=>{const c=e.$$.on_mount.map(P).filter(S);e.$$.on_destroy?e.$$.on_destroy.push(...c):h(c),e.$$.on_mount=[]}),s.forEach(b)}function X(e,t){const n=e.$$;n.fragment!==null&&(L(n.after_update),h(n.on_destroy),n.fragment&&n.fragment.d(t),n.on_destroy=n.fragment=null,n.ctx=[])}function Y(e,t){e.$$.dirty[0]===-1&&(T.push(e),D(),e.$$.dirty.fill(0)),e.$$.dirty[t/31|0]|=1<<t%31}function be(e,t,n,i,s,c,a=null,u=[-1]){const r=q;N(e);const l=e.$$={fragment:null,ctx:[],props:c,update:y,not_equal:s,bound:w(),on_mount:[],on_destroy:[],on_disconnect:[],before_update:[],after_update:[],context:new Map(t.context||(r?r.$$.context:[])),callbacks:w(),dirty:u,skip_bound:!1,root:t.target||r.$$.root};a&&a(l.root);let o=!1;if(l.ctx=n?n(e,t.props||{},(f,d,...g)=>{const v=g.length?g[0]:d;return l.ctx&&s(l.ctx[f],l.ctx[f]=v)&&(!l.skip_bound&&l.bound[f]&&l.bound[f](v),o&&Y(e,f)),d}):[],l.update(),o=!0,h(l.before_update),l.fragment=i?i(l.ctx):!1,t.target){if(t.hydrate){H();const f=V(t.target);l.fragment&&l.fragment.l(f),f.forEach(G)}else l.fragment&&l.fragment.c();t.intro&&K(e.$$.fragment),Q(e,t.target,t.anchor),M(),B()}N(r)}class Ne{constructor(){$(this,"$$");$(this,"$$set")}$destroy(){X(this,1),this.$destroy=y}$on(t,n){if(!S(n))return y;const i=this.$$.callbacks[t]||(this.$$.callbacks[t]=[]);return i.push(n),()=>{const s=i.indexOf(n);s!==-1&&i.splice(s,1)}}$set(t){this.$$set&&!I(t)&&(this.$$.skip_bound=!0,this.$$set(t),this.$$.skip_bound=!1)}}const Z="4";typeof window<"u"&&(window.__svelte||(window.__svelte={v:new Set})).v.add(Z);export{le as A,_e as B,pe as C,me as D,re as E,ae as F,he as G,Ne as S,V as a,J as b,ue as c,G as d,R as e,fe as f,te as g,F as h,be as i,oe as j,K as k,ge as l,ie as m,xe as n,se as o,de as p,ye as q,$e as r,ne as s,x as t,ve as u,we as v,Q as w,X as x,U as y,ce as z};