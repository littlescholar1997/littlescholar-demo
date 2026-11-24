import { test } from 'node:test';
import assert from 'node:assert/strict';
import { generateKeyPair, SignJWT, createLocalJWKSet, exportJWK } from 'jose';
import { createHandler, readConfig } from '../src/worker.mjs';
const env = {ACCESS_TEAM_DOMAIN:'https://school.cloudflareaccess.com',ACCESS_AUD:'cms-aud',ADMIN_EMAILS:'owner@example.test',ADMIN_ORIGIN:'https://admin.example.test',ASSETS:{fetch:async r=>new Response('asset:'+new URL(r.url).pathname)}};
const {publicKey,privateKey}=await generateKeyPair('RS256');
const jwk=await exportJWK(publicKey);jwk.kid='test-key';
const handler=createHandler({keyResolver:createLocalJWKSet({keys:[jwk]})});
async function token(claims={},options={}) {
 return new SignJWT({email:'owner@example.test',...claims}).setProtectedHeader({alg:'RS256',kid:'test-key'}).setIssuer(options.issuer||env.ACCESS_TEAM_DOMAIN).setAudience(options.audience||env.ACCESS_AUD).setSubject('google-or-otp-subject').setIssuedAt().setExpirationTime(options.exp||'1h').sign(privateKey);
}
async function req(path, jwt, init={}, environment=env) {
 const headers=new Headers(init.headers);if(jwt)headers.set('Cf-Access-Jwt-Assertion',jwt);
 return handler(new Request('https://admin.example.test'+path,{...init,headers}),environment);
}
test('empty or untrusted configuration fails closed',async()=>{
 assert.equal(readConfig({...env,ADMIN_EMAILS:''}),null);
 assert.equal(readConfig({...env,ACCESS_TEAM_DOMAIN:'https://evil.test'}),null);
 assert.equal((await req('/admin/workspace.html',null,{},{})).status,503);
});
test('no token, forged email, forged cookie, malformed token cannot read assets or session',async()=>{
 for(const path of ['/admin/workspace.html','/admin/admin.js','/content/site.json','/api/admin/session','/uploads/wix/a.webp']) {
  assert.equal((await req(path,null,{headers:{'Cf-Access-Authenticated-User-Email':'owner@example.test',Cookie:'CF_Authorization=fake'}})).status,401);
  assert.equal((await req(path,'fake')).status,401);
 }
});
test('wrong audience, issuer, expired token and non-admin identities are rejected',async()=>{
 for(const jwt of [await token({}, {audience:'other'}),await token({}, {issuer:'https://evil.test'}),await token({}, {exp:1}),await token({email:'outsider@example.test'})])assert.equal((await req('/api/admin/session',jwt)).status,401);
});
test('signature tampering and tokens without expiration fail',async()=>{
 const jwt=await token();const parts=jwt.split('.');parts[1]=Buffer.from(JSON.stringify({email:'owner@example.test',sub:'fake',exp:9999999999})).toString('base64url');
 assert.equal((await req('/api/admin/session',parts.join('.'))).status,401);
 const noExp=await new SignJWT({email:'owner@example.test'}).setProtectedHeader({alg:'RS256',kid:'test-key'}).setIssuer(env.ACCESS_TEAM_DOMAIN).setAudience(env.ACCESS_AUD).setSubject('subject').setIssuedAt().sign(privateKey);
 assert.equal((await req('/api/admin/session',noExp)).status,401);
});
test('allowed admin sees identity and workspace, never JWTs or secrets',async()=>{
 const jwt=await token({email:'OWNER@EXAMPLE.TEST'});const res=await req('/api/admin/session',jwt);const json=await res.json();
 assert.equal(json.user.email,'owner@example.test');assert.equal(json.authenticated,true);assert.equal(json.publishingEnabled,false);assert.ok(!JSON.stringify(json).includes(jwt));
 const asset=await req('/admin/workspace.html',jwt);assert.equal(await asset.text(),'asset:/admin/workspace.html');assert.match(asset.headers.get('Cache-Control'),/no-store/);assert.equal(asset.headers.get('X-Frame-Options'),'DENY');
});
test('origin pinning, removed admins, unsupported writes, demos and unknown APIs fail closed',async()=>{
 const jwt=await token();
 assert.equal((await handler(new Request('https://alternate.example.test/admin/workspace.html',{headers:{'Cf-Access-Jwt-Assertion':jwt}}),env)).status,403);
 assert.equal((await req('/api/admin/session',jwt,{}, {...env,ADMIN_EMAILS:'another@example.test'})).status,401);
 assert.equal((await req('/content/site.json',jwt,{method:'PUT',body:'overwrite'})).status,405);
 assert.equal((await req('/admin/demo.html',jwt)).status,404);
 assert.equal((await req('/api/admin/publish',jwt,{method:'POST'})).status,404);
});
test('logout requires authenticated POST and same origin; destination is fixed',async()=>{
 const jwt=await token();assert.equal((await req('/api/admin/logout',jwt)).status,405);
 assert.equal((await req('/api/admin/logout',jwt,{method:'POST',headers:{Origin:'https://evil.test'}})).status,403);
 const res=await req('/api/admin/logout',jwt,{method:'POST',headers:{Origin:env.ADMIN_ORIGIN}});
 assert.deepEqual(await res.json(),{logoutUrl:'https://admin.example.test/cdn-cgi/access/logout'});
});
test('root redirect and Wix media aliases stay same-origin and authenticated',async()=>{
 const jwt=await token();const redirect=await req('/',jwt);assert.equal(redirect.headers.get('Location'),env.ADMIN_ORIGIN+'/admin/workspace.html');
 assert.equal(await(await req('/littlescholar-demo/uploads/wix/abcdef.webp',jwt)).text(),'asset:/uploads/wix/abcdef.webp');
});
